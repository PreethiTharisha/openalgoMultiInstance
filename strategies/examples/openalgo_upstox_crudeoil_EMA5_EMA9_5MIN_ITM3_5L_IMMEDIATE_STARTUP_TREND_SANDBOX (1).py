#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Upstox + OpenAlgo + MCX CRUDEOIL
EMA5 / EMA9 - 5 Minute - ITM3 - Rs.5L Full Capacity
Analyzer/Sandbox orders only
Startup existing-trend enabled
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, date, timedelta, time as dtime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests

IST = ZoneInfo("Asia/Kolkata")
HOST = os.getenv("HOST_SERVER", "http://127.0.0.1:5002").strip()
API_KEY = os.getenv("OPENALGO_API_KEY", "").strip()

STRATEGY_NAME = "UPSTOX_CRUDEOIL_EMA5_EMA9_5MIN_ITM3_5L_IMMEDIATE_STARTUP_TREND_SANDBOX"

EXCHANGE = "MCX"
UNDERLYING = "CRUDEOIL"
PRODUCT = "NRML"

EMA_FAST = 5
EMA_SLOW = 9
INTERVAL = "5m"
HISTORY_LOOKBACK_DAYS = 5
ITM_STEPS = 3

TRADING_CAPITAL_RUPEES = 500000.0
HARD_STOP_PERCENT = 5.0


NO_NEW_ORDERS_AT = dtime(23, 29)
FORCE_SQUARE_OFF_AT = dtime(23, 29)
MAIN_POLL_SECONDS = 1.0


class OpenAlgoError(RuntimeError):
    pass


def now_ist() -> datetime:
    return datetime.now(IST)


def log(msg: str) -> None:
    stamp = now_ist().strftime("%Y-%m-%d %H:%M:%S IST")
    line = f"[{stamp}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"), flush=True)


session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


def post(path: str, payload: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
    url = HOST.rstrip("/") + path
    try:
        r = session.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise OpenAlgoError(f"Connection error calling {path}: {exc}") from exc

    try:
        data = r.json()
    except Exception:
        raise OpenAlgoError(
            f"{path} HTTP {r.status_code}, non-JSON response: {r.text[:500]}"
        )

    if r.status_code >= 400:
        raise OpenAlgoError(f"{path} HTTP {r.status_code}: {data}")

    return data


def validate_config() -> None:
    if not API_KEY:
        raise SystemExit("OPENALGO_API_KEY is not set.")
    if not 1 <= len(API_KEY) <= 256:
        raise SystemExit(f"Invalid OPENALGO_API_KEY length: {len(API_KEY)}")

    log(f"OpenAlgo API key loaded: length={len(API_KEY)} (value hidden)")
    log(
        f"CONFIG: capital=Rs.{TRADING_CAPITAL_RUPEES:,.0f} "
        f"| EMA={EMA_FAST}/{EMA_SLOW} | interval={INTERVAL} "
        f"| hard_stop={HARD_STOP_PERCENT:.1f}% | ITM={ITM_STEPS}"
    )


def force_analyzer_mode() -> None:
    log("SAFETY: forcing Analyzer Mode ON...")
    resp = post(
        "/api/v1/analyzer/toggle",
        {"apikey": API_KEY, "mode": True},
    )
    log(f"Analyzer toggle: {resp}")
    verify_analyzer_mode()
    log("SAFETY VERIFIED: Analyzer Mode is ON.")


def verify_analyzer_mode() -> None:
    resp = post("/api/v1/analyzer", {"apikey": API_KEY})
    data = resp.get("data") or {}
    if not bool(data.get("analyze_mode")):
        raise OpenAlgoError("ORDER BLOCKED: Analyzer Mode is OFF.")


def place_order(symbol: str, action: str, quantity: int) -> Dict[str, Any]:
    verify_analyzer_mode()

    resp = post(
        "/api/v1/placeorder",
        {
            "apikey": API_KEY,
            "strategy": STRATEGY_NAME,
            "symbol": symbol,
            "action": action,
            "exchange": EXCHANGE,
            "pricetype": "MARKET",
            "product": PRODUCT,
            "quantity": str(int(quantity)),
        },
    )

    if resp.get("status") != "success":
        raise OpenAlgoError(f"{action} order failed: {resp}")

    if resp.get("mode") not in (None, "analyze"):
        raise OpenAlgoError(f"Unexpected order mode: {resp}")

    return resp


def search_symbols(query: str) -> List[Dict[str, Any]]:
    resp = post(
        "/api/v1/search",
        {
            "apikey": API_KEY,
            "query": query,
            "exchange": EXCHANGE,
        },
    )
    if resp.get("status") != "success":
        raise OpenAlgoError(f"Search failed: {resp}")
    return resp.get("data") or []


def quote(symbol: str) -> Dict[str, Any]:
    resp = post(
        "/api/v1/quotes",
        {
            "apikey": API_KEY,
            "symbol": symbol,
            "exchange": EXCHANGE,
        },
    )
    if resp.get("status") != "success":
        raise OpenAlgoError(f"Quote failed for {symbol}: {resp}")
    return resp.get("data") or {}


def ltp(symbol: str) -> float:
    value = quote(symbol).get("ltp")
    if value is None:
        raise OpenAlgoError(f"No LTP returned for {symbol}")
    return float(value)


def parse_expiry(value: Any) -> Optional[date]:
    if value is None:
        return None
    text = str(value).strip().upper()
    for fmt in ("%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def is_main_crude(row: Dict[str, Any]) -> bool:
    symbol = str(row.get("symbol") or "").upper()
    name = str(row.get("name") or "").upper()
    return (
        name == UNDERLYING
        or (
            symbol.startswith(UNDERLYING)
            and not symbol.startswith("CRUDEOILM")
        )
    )


def nearest_future(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    today = now_ist().date()
    candidates: List[Tuple[date, str, Dict[str, Any]]] = []

    for row in rows:
        if not is_main_crude(row):
            continue

        symbol = str(row.get("symbol") or "").upper()
        itype = str(row.get("instrumenttype") or "").upper()
        expiry = parse_expiry(row.get("expiry"))

        is_future = (
            itype in {"FUT", "FUTCOM", "FUTURES"}
            or symbol.endswith("FUT")
        )

        if is_future and expiry and expiry >= today:
            candidates.append((expiry, symbol, row))

    if not candidates:
        raise OpenAlgoError("No active CRUDEOIL future found.")

    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


def history(symbol: str) -> List[Dict[str, Any]]:
    today = now_ist().date()

    resp = post(
        "/api/v1/history",
        {
            "apikey": API_KEY,
            "symbol": symbol,
            "exchange": EXCHANGE,
            "interval": INTERVAL,
            "start_date": (today - timedelta(days=HISTORY_LOOKBACK_DAYS)).isoformat(),
            "end_date": today.isoformat(),
        },
    )

    if resp.get("status") != "success":
        raise OpenAlgoError(f"History failed: {resp}")

    raw = resp.get("data") or []
    cleaned: List[Dict[str, Any]] = []

    for row in raw:
        try:
            cleaned.append(
                {
                    "timestamp": int(row["timestamp"]),
                    "close": float(row["close"]),
                }
            )
        except Exception:
            pass

    cleaned.sort(key=lambda x: x["timestamp"])
    return cleaned


def ema(values: List[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = [None] * len(values)

    if len(values) < period:
        return result

    seed = sum(values[:period]) / period
    result[period - 1] = seed

    alpha = 2.0 / (period + 1.0)
    prev = seed

    for i in range(period, len(values)):
        prev = alpha * values[i] + (1.0 - alpha) * prev
        result[i] = prev

    return result


def detect_cross(closes: List[float]) -> Tuple[Optional[str], float, float]:
    if len(closes) < EMA_SLOW + 1:
        return None, float("nan"), float("nan")

    fast = ema(closes, EMA_FAST)
    slow = ema(closes, EMA_SLOW)

    f1, s1 = fast[-2], slow[-2]
    f0, s0 = fast[-1], slow[-1]

    if None in (f1, s1, f0, s0):
        return None, float("nan"), float("nan")

    f1 = float(f1)
    s1 = float(s1)
    f0 = float(f0)
    s0 = float(s0)

    if f1 <= s1 and f0 > s0:
        return "BULL", f0, s0

    if f1 >= s1 and f0 < s0:
        return "BEAR", f0, s0

    return None, f0, s0


def current_regime(closes: List[float]) -> Tuple[Optional[str], float, float]:
    if len(closes) < EMA_SLOW:
        return None, float("nan"), float("nan")

    fast = ema(closes, EMA_FAST)
    slow = ema(closes, EMA_SLOW)

    f0, s0 = fast[-1], slow[-1]
    if None in (f0, s0):
        return None, float("nan"), float("nan")

    f0 = float(f0)
    s0 = float(s0)

    if f0 > s0:
        return "BULL", f0, s0
    if f0 < s0:
        return "BEAR", f0, s0

    return None, f0, s0


def option_rows(
    rows: List[Dict[str, Any]],
    side: str,
) -> List[Tuple[date, float, Dict[str, Any]]]:
    today = now_ist().date()
    side = side.upper()
    result: List[Tuple[date, float, Dict[str, Any]]] = []

    for row in rows:
        if not is_main_crude(row):
            continue

        symbol = str(row.get("symbol") or "").upper()
        itype = str(row.get("instrumenttype") or "").upper()
        expiry = parse_expiry(row.get("expiry"))

        is_side = (
            itype == side
            or (side == "CE" and symbol.endswith("CE"))
            or (side == "PE" and symbol.endswith("PE"))
        )

        if not is_side or not expiry or expiry < today:
            continue

        try:
            strike = float(row.get("strike"))
        except Exception:
            continue

        if strike > 0:
            result.append((expiry, strike, row))

    return result


def choose_itm3(
    rows: List[Dict[str, Any]],
    side: str,
    future_price: float,
) -> Dict[str, Any]:
    candidates = option_rows(rows, side)

    if not candidates:
        raise OpenAlgoError(f"No active CRUDEOIL {side} option found.")

    nearest_expiry = min(exp for exp, _, _ in candidates)

    same_expiry = [
        (strike, row)
        for exp, strike, row in candidates
        if exp == nearest_expiry
    ]

    strikes = sorted({strike for strike, _ in same_expiry})

    atm_index = min(
        range(len(strikes)),
        key=lambda i: abs(strikes[i] - future_price),
    )

    target_index = atm_index - ITM_STEPS if side == "CE" else atm_index + ITM_STEPS

    if target_index < 0 or target_index >= len(strikes):
        raise OpenAlgoError("ITM3 strike unavailable.")

    target_strike = strikes[target_index]

    exact = [
        row
        for strike, row in same_expiry
        if abs(strike - target_strike) < 1e-9
    ]

    if not exact:
        raise OpenAlgoError("ITM3 option row not found.")

    selected = exact[0]

    log(
        f"OPTION: side={side} expiry={nearest_expiry} "
        f"FUT={future_price:.2f} ATM={strikes[atm_index]:g} "
        f"ITM3={target_strike:g} symbol={selected.get('symbol')} "
        f"lot={selected.get('lotsize')}"
    )

    return selected


def full_capacity_quantity(
    option_price: float,
    lot_size: int,
) -> Tuple[int, int]:
    cost_per_lot = option_price * lot_size
    lots = int(TRADING_CAPITAL_RUPEES // cost_per_lot)

    if lots < 1:
        raise OpenAlgoError(
            f"Rs.5L insufficient for one lot: "
            f"option_price={option_price:.2f}, lot_size={lot_size}, "
            f"cost_per_lot=Rs.{cost_per_lot:,.0f}"
        )

    quantity = lots * lot_size
    deployment = option_price * quantity

    log(
        f"FULL CAPACITY: option_price={option_price:.2f} "
        f"| lot_size={lot_size} | lots={lots} | qty={quantity} "
        f"| deployment=Rs.{deployment:,.0f}"
    )

    return lots, quantity


@dataclass
class Position:
    direction: str
    option_type: str
    symbol: str
    quantity: int
    entry_price: float


position: Optional[Position] = None


def enter_option(
    direction: str,
    rows: List[Dict[str, Any]],
    future_symbol: str,
) -> Position:
    future_price = ltp(future_symbol)
    side = "CE" if direction == "BULL" else "PE"

    inst = choose_itm3(rows, side, future_price)
    symbol = str(inst.get("symbol") or "").upper()

    lot_size = int(float(inst.get("lotsize") or 0))
    if lot_size <= 0:
        raise OpenAlgoError(f"Invalid lot size for {symbol}")

    option_price = ltp(symbol)
    lots, quantity = full_capacity_quantity(option_price, lot_size)

    log(
        f"ENTRY {direction}: {symbol} "
        f"price={option_price:.2f} lots={lots} qty={quantity}"
    )

    resp = place_order(symbol, "BUY", quantity)
    log(f"SANDBOX BUY: {resp}")

    time.sleep(0.5)

    try:
        entry_price = ltp(symbol)
    except Exception:
        entry_price = option_price

    return Position(
        direction=direction,
        option_type=side,
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
    )


def exit_position(reason: str) -> None:
    global position

    if position is None:
        return

    log(f"EXIT {reason}: {position.symbol} qty={position.quantity}")

    resp = place_order(
        position.symbol,
        "SELL",
        position.quantity,
    )

    log(f"SANDBOX SELL: {resp}")
    position = None


def hard_stop_check() -> None:
    if position is None:
        return

    current = ltp(position.symbol)
    pnl_percent = (
        (current - position.entry_price)
        / position.entry_price
        * 100.0
    )

    log(
        f"POSITION {position.symbol} "
        f"entry={position.entry_price:.2f} "
        f"ltp={current:.2f} pnl={pnl_percent:+.2f}%"
    )

    if pnl_percent <= -HARD_STOP_PERCENT:
        exit_position("HARD_STOP_5PCT")


def main() -> int:
    global position

    log("=" * 90)
    log("UPSTOX CRUDEOIL EMA5/EMA9 5MIN ITM3 Rs.5L IMMEDIATE + STARTUP TREND - SANDBOX")
    log("=" * 90)

    validate_config()
    force_analyzer_mode()

    rows = search_symbols(UNDERLYING)
    log(f"Search returned {len(rows)} CRUDEOIL-related MCX rows.")

    future = nearest_future(rows)
    future_symbol = str(future.get("symbol") or "").upper()

    log(
        f"FUTURE SELECTED: {future_symbol} "
        f"expiry={future.get('expiry')} lot={future.get('lotsize')}"
    )

    hist = history(future_symbol)

    closes: List[Tuple[int, float]] = []

    for row in hist:
        ts = int(row["timestamp"])
        close = float(row["close"])

        if closes and closes[-1][0] == ts:
            closes[-1] = (ts, close)
        else:
            closes.append((ts, close))

    if len(closes) > 500:
        closes = closes[-500:]

    if not closes:
        raise OpenAlgoError("No 5-minute history available.")

    log(f"Loaded {len(closes)} historical 5-minute candles.")

    startup_values = [x[1] for x in closes]
    startup_regime, startup_ema5, startup_ema9 = current_regime(startup_values)

    if now_ist().time().replace(tzinfo=None) < NO_NEW_ORDERS_AT:
        if startup_regime == "BULL" and position is None:
            log(
                f"STARTUP EXISTING TREND: EMA5={startup_ema5:.4f} > "
                f"EMA9={startup_ema9:.4f} -> bullish regime already active. "
                "Buying CALL immediately without waiting for a fresh crossover."
            )
            position = enter_option(
                "BULL",
                rows,
                future_symbol,
            )

        elif startup_regime == "BEAR" and position is None:
            log(
                f"STARTUP EXISTING TREND: EMA5={startup_ema5:.4f} < "
                f"EMA9={startup_ema9:.4f} -> bearish regime already active. "
                "Buying PUT immediately without waiting for a fresh crossover."
            )
            position = enter_option(
                "BEAR",
                rows,
                future_symbol,
            )
        else:
            log(
                f"STARTUP REGIME: no actionable startup position "
                f"(regime={startup_regime}, EMA5={startup_ema5:.4f}, EMA9={startup_ema9:.4f})."
            )
    else:
        log("STARTUP ENTRY SKIPPED: entry cutoff already reached.")

    last_history_ts = closes[-1][0]

    while True:
        current_time = now_ist().time().replace(tzinfo=None)

        if current_time >= FORCE_SQUARE_OFF_AT:
            if position is not None:
                exit_position("23_29_FORCE_SQUARE_OFF")

            log("23:29 IST reached. No new orders. Strategy stopped.")
            break

        if position is not None:
            try:
                hard_stop_check()
            except Exception as exc:
                log(f"STOP CHECK ERROR: {exc}")

        try:
            latest_history = history(future_symbol)
        except Exception as exc:
            log(f"HISTORY ERROR: {exc}")
            time.sleep(MAIN_POLL_SECONDS)
            continue

        fresh_rows = []

        for row in latest_history:
            try:
                ts = int(row["timestamp"])
                close = float(row["close"])
            except Exception:
                continue

            if ts > last_history_ts:
                fresh_rows.append((ts, close))

        if fresh_rows:
            fresh_rows.sort(key=lambda x: x[0])

            for ts, close in fresh_rows:
                closes.append((ts, close))
                last_history_ts = ts

                if len(closes) > 500:
                    closes = closes[-500:]

                values = [x[1] for x in closes]
                signal, ema5_value, ema9_value = detect_cross(values)

                candle_time = datetime.fromtimestamp(ts, IST)

                log(
                    f"5MIN CANDLE {candle_time.strftime('%H:%M')} "
                    f"C={close:.2f} "
                    f"EMA5={ema5_value:.4f} "
                    f"EMA9={ema9_value:.4f} "
                    f"cross={signal}"
                )

                if signal is None:
                    continue

                if now_ist().time().replace(tzinfo=None) >= NO_NEW_ORDERS_AT:
                    continue

                if signal == "BULL":
                    log("BULL CROSS CONFIRMED ON CLOSED 5MIN CANDLE: acting immediately.")

                    if position is not None and position.option_type == "PE":
                        exit_position("BULL_CROSS_SELL_PUT")

                    if position is None:
                        position = enter_option(
                            "BULL",
                            rows,
                            future_symbol,
                        )

                elif signal == "BEAR":
                    log("BEAR CROSS CONFIRMED ON CLOSED 5MIN CANDLE: acting immediately.")

                    if position is not None and position.option_type == "CE":
                        exit_position("BEAR_CROSS_SELL_CALL")

                    if position is None:
                        position = enter_option(
                            "BEAR",
                            rows,
                            future_symbol,
                        )

        time.sleep(MAIN_POLL_SECONDS)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("Stopped by user. Check Analyzer positions/orderbook.")
        raise
    except Exception as exc:
        log(f"FATAL ERROR: {type(exc).__name__}: {exc}")
        raise
