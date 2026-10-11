#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
5PAISA + OPENALGO + MCX CRUDEOIL
DYNAMIC-OPTION V8 TRUE30SEC - EMA12/EMA41 - 30 SECOND - Rs.50K - ANALYZER/SANDBOX ONLY

This is a conservative test strategy. It cannot guarantee profit.

CORE SIGNAL
-----------
Dynamic traded symbol:
- The nearest active CRUDEOIL future is the underlying/reference.
- Current future price determines ATM from the listed option strikes.
- Bullish reference trend -> select nearest-expiry ITM3 CE.
- Bearish reference trend -> select nearest-expiry ITM3 PE.
- The selected option must then pass its OWN EMA12/EMA41 confirmation.

A trade is NOT taken merely because the underlying EMA points in one direction.

Fresh BUY / re-BUY requires ALL of the following:
1. Underlying nearest CRUDEOIL future establishes direction:
   CE -> FUT EMA12 > EMA41
   PE -> FUT EMA12 < EMA41
2. Underlying RSI confirms:
   CE -> RSI >= 55
   PE -> RSI <= 45
3. Underlying ADX >= 20
4. Underlying ATR% >= minimum volatility
5. Underlying breaks recent 3 x 30-second high/low
6. Underlying direction persists for 2 consecutive completed 30-second candles
7. Dynamically selected option passes its OWN EMA12/EMA41:
   - selected option EMA12 > EMA41
   - EMA12 slope positive
   - minimum EMA separation
8. Pre-entry live option check:
   - live price still supports direction
   - no excessive 2-second price jump/chase
9. Existing CRUDEOIL option positions must be flat before BUY.

AFTER BUY
---------
- The exact purchased option symbol is monitored independently.
- Its own local 30-second EMA12/EMA41 is maintained.
- If the purchased option EMA12 crosses below EMA41, the position is exited.
- Underlying/reference EMA is also monitored. If underlying direction reverses,
  the position is exited.
- Manual exit remains supported: after manual exit the strategy may select a new
  dynamic symbol and re-enter when the full conditions pass again.

RISK / EXIT
-----------
- Maximum premium deployment per trade: Rs.50,000.
- Dynamic lots based on live option price.
- HARD STOP: -5.0% from actual positionbook average entry.
- SOFT LOSS GUARD:
    if PnL <= -2.5% AND current signal quality has deteriorated,
    exit before hard stop.
- LOSS DRAWDOWN GUARD:
    before the +20% lock activates, if the trade gives back >= 2.5
    percentage points from its best PnL and current PnL <= -2.0%, exit.
- PROFIT LADDER:
    activate protection at +10%.
    +10% to +15% zone keeps a fixed +10% floor.
    from +15% onward, use a 5%-step ladder / trailing floor.
    Example:
      peak +20% -> floor +15%
      peak +25% -> floor +20%
      peak +30% -> floor +25%
- EMA/signal reversal exit still applies.
- Every SELL starts a 5-minute global cooldown.
- Loss exit additionally blocks re-entry in the SAME direction for 10 minutes.
- Two consecutive loss exits trigger a 15-minute global loss pause.
- Three hard-stop exits disable NEW entries for the rest of the script session.
- MANUAL/EXTERNAL EXIT SUPPORT:
    if the tracked CE/PE disappears from positionbook without a script SELL,
    it is treated as a manual/external exit.
    It does NOT create a new cooldown or count as a loss.
    The bot may re-enter on the next completed 30-second decision bar when
    all entry-quality filters are satisfied.
- At/after 23:29 IST square off all long CRUDEOIL options.
- No new entries at/after 23:28 IST.

DATA
----
- Option signal candles: local completed 30-second candles.
- Underlying filter candles: local completed 30-second CRUDEOIL FUT candles.
- 1-minute history is used ONLY to warm EMAs at startup.
- Analyzer Mode is forced ON and verified before each order.
"""

from __future__ import annotations

import os
import time
import math
import re
from dataclasses import dataclass
from datetime import datetime, date, timedelta, time as dtime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests


# =============================================================================
# CONFIG
# =============================================================================

IST = ZoneInfo("Asia/Kolkata")

HOST = os.getenv("HOST_SERVER", "http://127.0.0.1:5005").strip()
API_KEY = os.getenv("OPENALGO_API_KEY", "").strip()

STRATEGY_NAME = (
    "5PAISA_CRUDEOIL_EMA12_EMA41_30SEC_"
    "PROFIT_BIAS_V4_50K_HARD5_SANDBOX"
)

EXCHANGE = "MCX"
PRODUCT = "NRML"
UNDERLYING = "CRUDEOIL"

# Dynamic option selection
# Direction comes from the nearest active CRUDEOIL future.
# Bullish -> nearest-expiry ITM CE
# Bearish -> nearest-expiry ITM PE
ITM_STEPS = 3
OPTION_SEARCH_MAX_ROWS = 500

EMA_FAST = 12
EMA_SLOW = 41
CANDLE_SECONDS = 30

CAPITAL_RUPEES = 50_000.0

# Entry quality
OPTION_MIN_EMA_SEPARATION_PCT = 0.30
FUTURE_MIN_EMA_SEPARATION_PCT = 0.04
SIGNAL_PERSIST_BARS = 2

RSI_PERIOD = 14
RSI_BULL_MIN = 55.0
RSI_BEAR_MAX = 45.0

ADX_PERIOD = 14
ADX_MIN = 20.0

ATR_PERIOD = 14
ATR_MIN_PCT = 0.05

BREAKOUT_LOOKBACK = 3

# Avoid buying after a sudden premium spike / poor chase.
MAX_PREENTRY_JUMP_PCT = 1.50
MAX_OPTION_DISTANCE_FROM_EMA12_PCT = 3.00
PREENTRY_SAMPLE_SECONDS = 2.0

# Risk / profit
HARD_STOP_PCT = -5.0
SOFT_LOSS_GUARD_PCT = -2.5
LOSS_DRAWDOWN_TRIGGER_PCT = -2.0
LOSS_DRAWDOWN_FROM_PEAK_PCT = 2.5

# Profit ladder:
# 1) Once peak reaches +10%, protect a minimum +10%.
# 2) Between +10% and +15%, floor stays fixed at +10%.
# 3) Once peak reaches +15%, ladder trailing begins with a 5 percentage-point gap.
#    Peak +15% to <20% => floor +10%
#    Peak +20% to <25% => floor +15%
#    Peak +25% to <30% => floor +20%
#    Peak +30% to <35% => floor +25%, and so on.
# The floor never moves downward.
PROFIT_LOCK_TRIGGER_PCT = 10.0
PROFIT_LADDER_START_PCT = 15.0
PROFIT_LADDER_STEP_PCT = 5.0
PROFIT_TRAIL_GAP_PCT = 5.0

# Cooldowns
GLOBAL_COOLDOWN_SECONDS = 5 * 60
SAME_SIDE_LOSS_COOLDOWN_SECONDS = 10 * 60
CONSECUTIVE_LOSS_PAUSE_SECONDS = 15 * 60
CONSECUTIVE_LOSS_TRIGGER = 2
MAX_HARD_STOPS_PER_SESSION = 3

ENTRY_CUTOFF = dtime(23, 28)
FORCE_EXIT_AT = dtime(23, 29)

QUOTE_TIMEOUT = 3
ORDER_TIMEOUT = 8
POLL_SECONDS = 1.0
HISTORY_LOOKBACK_DAYS = 3

# Warm-up reliability
HISTORY_RETRY_COUNT = 3
HISTORY_RETRY_DELAY_SECONDS = 1.0
MIN_EMA_READY_CLOSES = EMA_SLOW + 3

# Fallback EMA seed if /history is temporarily unavailable.
# The fallback uses repeated live samples only as startup seed and is NEVER
# treated as a genuine 30-second signal series.
FALLBACK_SEED_SAMPLES = EMA_SLOW + 3
FALLBACK_SEED_SAMPLE_DELAY = 0.25

session = requests.Session()

# Best-effort UTF-8 console setup for Windows.
# If unsupported, the safe logger above still prevents Unicode crashes.
try:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(
            encoding="utf-8",
            errors="replace",
        )

    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(
            encoding="utf-8",
            errors="replace",
        )
except Exception:
    pass


# =============================================================================
# BASIC
# =============================================================================

class OpenAlgoError(RuntimeError):
    pass


def now_ist() -> datetime:
    return datetime.now(IST)


def log(msg: str) -> None:
    """
    Windows-safe logger.

    Some Windows terminals use CP1252 instead of UTF-8. Any unsupported
    character is replaced instead of crashing the trading loop.
    """
    line = f"[{now_ist().strftime('%Y-%m-%d %H:%M:%S IST')}] {msg}"

    try:
        print(
            line,
            flush=True,
        )
    except UnicodeEncodeError:
        import sys

        encoding = (
            getattr(
                sys.stdout,
                "encoding",
                None,
            )
            or "cp1252"
        )

        safe_line = (
            line
            .encode(
                encoding,
                errors="replace",
            )
            .decode(
                encoding,
                errors="replace",
            )
        )

        print(
            safe_line,
            flush=True,
        )


def require_api_key() -> None:
    if not API_KEY:
        raise OpenAlgoError(
            "OPENALGO_API_KEY is not set for this OpenAlgo instance."
        )


def post(
    path: str,
    payload: Dict[str, Any],
    timeout: int = 8,
) -> Dict[str, Any]:
    url = HOST.rstrip("/") + path

    try:
        r = session.post(
            url,
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OpenAlgoError(
            f"Connection error calling {path}: {exc}"
        ) from exc

    try:
        data = r.json()
    except Exception:
        raise OpenAlgoError(
            f"{path} HTTP {r.status_code}, non-JSON: {r.text[:500]}"
        )

    if r.status_code >= 400:
        raise OpenAlgoError(
            f"{path} HTTP {r.status_code}: {data}"
        )

    return data


# =============================================================================
# ANALYZER SAFETY
# =============================================================================

def verify_analyzer() -> None:
    response = post(
        "/api/v1/analyzer",
        {"apikey": API_KEY},
    )

    data = response.get("data") or {}

    if not bool(data.get("analyze_mode")):
        raise OpenAlgoError(
            "ORDER BLOCKED: OpenAlgo Analyzer Mode is OFF."
        )


def force_analyzer() -> None:
    response = post(
        "/api/v1/analyzer/toggle",
        {
            "apikey": API_KEY,
            "mode": True,
        },
    )

    log(f"Analyzer toggle: {response}")
    verify_analyzer()
    log("SAFETY VERIFIED: OpenAlgo Analyzer Mode is ON.")


# =============================================================================
# MARKET DATA
# =============================================================================

def quote(symbol: str) -> Dict[str, Any]:
    return post(
        "/api/v1/quotes",
        {
            "apikey": API_KEY,
            "symbol": symbol,
            "exchange": EXCHANGE,
        },
        timeout=QUOTE_TIMEOUT,
    )


def extract_ltp(data: Dict[str, Any]) -> float:
    candidates: List[Any] = []

    d = data.get("data")

    if isinstance(d, dict):
        candidates.extend(
            [
                d.get("ltp"),
                d.get("last_price"),
                d.get("last"),
                d.get("close"),
            ]
        )

    candidates.extend(
        [
            data.get("ltp"),
            data.get("last_price"),
            data.get("last"),
            data.get("close"),
        ]
    )

    for v in candidates:
        try:
            x = float(v)
            if x > 0:
                return x
        except Exception:
            pass

    raise OpenAlgoError(
        f"Could not extract LTP from quote response: {data}"
    )


def ltp(symbol: str) -> float:
    return extract_ltp(
        quote(symbol)
    )


def search_crudeoil_rows() -> List[Dict[str, Any]]:
    data = post(
        "/api/v1/search",
        {
            "apikey": API_KEY,
            "query": UNDERLYING,
            "exchange": EXCHANGE,
        },
    )

    rows = (
        data.get("data")
        or data.get("results")
        or data.get("symbols")
        or []
    )

    if isinstance(rows, dict):
        rows = (
            rows.get("data")
            or rows.get("results")
            or []
        )

    if not isinstance(rows, list):
        return []

    clean: List[Dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        sym = str(
            row.get("symbol")
            or ""
        ).upper()

        if "CRUDEOIL" not in sym:
            continue

        if "CRUDEOILM" in sym:
            continue

        clean.append(row)

    return clean


def parse_expiry(value: Any) -> Optional[date]:
    if value is None:
        return None

    text = str(value).strip()

    for fmt in (
        "%d-%b-%y",
        "%d-%b-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(
                text,
                fmt,
            ).date()
        except Exception:
            pass

    return None


def nearest_active_future(
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    today = now_ist().date()
    candidates: List[
        Tuple[date, Dict[str, Any]]
    ] = []

    for row in rows:
        sym = str(
            row.get("symbol")
            or ""
        ).upper()

        if not sym.endswith("FUT"):
            continue

        exp = parse_expiry(
            row.get("expiry")
        )

        if exp is None or exp < today:
            continue

        candidates.append(
            (exp, row)
        )

    if not candidates:
        raise OpenAlgoError(
            "No active CRUDEOIL future found."
        )

    candidates.sort(
        key=lambda x: x[0]
    )

    return candidates[0][1]


def lot_size_for_symbol(
    rows: List[Dict[str, Any]],
    symbol: str,
) -> int:
    target = symbol.upper()

    for row in rows:
        if str(
            row.get("symbol")
            or ""
        ).upper() != target:
            continue

        for key in (
            "lotsize",
            "lot_size",
            "lot",
            "lots",
        ):
            try:
                value = int(
                    float(
                        row.get(key)
                    )
                )

                if value > 0:
                    return value

            except Exception:
                pass

    log(
        f"WARNING: lot size metadata missing for {symbol}; "
        "using fallback 100."
    )

    return 100



def option_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    for row in rows:
        sym = str(row.get("symbol") or "").upper()

        if "CRUDEOILM" in sym or "CRUDEOIL" not in sym:
            continue

        if not (sym.endswith("CE") or sym.endswith("PE")):
            continue

        exp = parse_expiry(row.get("expiry"))

        if exp is None or exp < now_ist().date():
            continue

        out.append(row)

    return out


def strike_from_row(row: Dict[str, Any]) -> Optional[float]:
    for key in ("strike", "strike_price", "strikeprice"):
        try:
            x = float(row.get(key))
            if x > 0:
                return x
        except Exception:
            pass

    # Fallback parse from symbol: ...<strike>CE / ...<strike>PE
    sym = str(row.get("symbol") or "").upper()

    m = re.search(r"(\d+(?:\.\d+)?)(CE|PE)$", sym)

    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass

    return None


def resolve_dynamic_option(
    rows: List[Dict[str, Any]],
    direction: str,
    underlying_price: float,
) -> Dict[str, Any]:
    """
    Select nearest-expiry ITM3 option from listed CRUDEOIL contracts.

    BULLISH => CE, ITM strikes are below spot/future.
    BEARISH => PE, ITM strikes are above spot/future.
    """
    side = "CE" if direction == "BULLISH" else "PE"

    opts = [
        r for r in option_rows(rows)
        if str(r.get("symbol") or "").upper().endswith(side)
    ]

    if not opts:
        raise OpenAlgoError(f"No active CRUDEOIL {side} options found.")

    expiries = sorted(
        {
            parse_expiry(r.get("expiry"))
            for r in opts
            if parse_expiry(r.get("expiry")) is not None
        }
    )

    if not expiries:
        raise OpenAlgoError(f"No valid expiry found for CRUDEOIL {side}.")

    nearest_expiry = expiries[0]

    chain = [
        r for r in opts
        if parse_expiry(r.get("expiry")) == nearest_expiry
    ]

    strike_map: Dict[float, Dict[str, Any]] = {}

    for row in chain:
        strike = strike_from_row(row)
        if strike is not None:
            strike_map[strike] = row

    strikes = sorted(strike_map.keys())

    if not strikes:
        raise OpenAlgoError(
            f"No usable strikes found for CRUDEOIL {side} expiry={nearest_expiry}."
        )

    atm = min(
        strikes,
        key=lambda x: abs(x - underlying_price),
    )

    atm_idx = strikes.index(atm)

    if direction == "BULLISH":
        target_idx = max(0, atm_idx - ITM_STEPS)
    else:
        target_idx = min(len(strikes) - 1, atm_idx + ITM_STEPS)

    target_strike = strikes[target_idx]
    selected = strike_map[target_strike]

    log(
        f"DYNAMIC OPTION RESOLVED: direction={direction} side={side} "
        f"| FUT={underlying_price:.2f} | expiry={nearest_expiry} "
        f"| ATM={atm:g} | ITM{ITM_STEPS}={target_strike:g} "
        f"| symbol={str(selected.get('symbol') or '').upper()}"
    )

    return selected


def direction_from_future(
    fut_closes: List[float],
) -> Optional[str]:
    m = ema_metrics(fut_closes)

    if not m.get("ready"):
        return None

    if m["regime"] == "BULLISH":
        return "BULLISH"

    if m["regime"] == "BEARISH":
        return "BEARISH"

    return None


def history_seed_with_retry(
    symbol: str,
) -> List[float]:
    last_error: Optional[Exception] = None

    for attempt in range(
        1,
        HISTORY_RETRY_COUNT + 1,
    ):
        try:
            closes = history_seed(symbol)

            if len(closes) >= MIN_EMA_READY_CLOSES:
                log(
                    f"HISTORY WARMUP OK {symbol}: "
                    f"{len(closes)} closes on attempt {attempt}."
                )
                return closes

            log(
                f"HISTORY WARMUP INSUFFICIENT {symbol}: "
                f"{len(closes)} closes on attempt {attempt}."
            )

        except Exception as exc:
            last_error = exc

            log(
                f"HISTORY WARMUP RETRY {symbol}: "
                f"attempt {attempt}/{HISTORY_RETRY_COUNT} failed: {exc}"
            )

        if attempt < HISTORY_RETRY_COUNT:
            time.sleep(HISTORY_RETRY_DELAY_SECONDS)

    if last_error is not None:
        log(
            f"HISTORY WARMUP FAILED {symbol} after "
            f"{HISTORY_RETRY_COUNT} attempts: {last_error}"
        )

    return []


def fallback_live_seed(
    symbol: str,
) -> List[float]:
    """
    Temporary startup seed only.

    This prevents waiting ~22 minutes for EMA41 when /history is down.
    It does NOT create trade signals by itself. Genuine signal decisions
    still require completed local 30-second candles after startup.
    """
    samples: List[float] = []

    log(
        f"FALLBACK LIVE SEED START {symbol}: "
        f"collecting {FALLBACK_SEED_SAMPLES} quote samples."
    )

    for _ in range(FALLBACK_SEED_SAMPLES):
        try:
            samples.append(ltp(symbol))
        except Exception as exc:
            log(
                f"FALLBACK SEED QUOTE WARNING {symbol}: {exc}"
            )

        time.sleep(FALLBACK_SEED_SAMPLE_DELAY)

    log(
        f"FALLBACK LIVE SEED DONE {symbol}: "
        f"{len(samples)} samples collected."
    )

    return samples



def history_seed(
    symbol: str,
) -> List[float]:
    today = now_ist().date()

    data = post(
        "/api/v1/history",
        {
            "apikey": API_KEY,
            "symbol": symbol,
            "exchange": EXCHANGE,
            "interval": "1m",
            "start_date": (
                today
                - timedelta(
                    days=HISTORY_LOOKBACK_DAYS
                )
            ).isoformat(),
            "end_date": today.isoformat(),
        },
        timeout=5,
    )

    rows = data.get("data") or []

    if isinstance(rows, dict):
        rows = (
            rows.get("candles")
            or rows.get("data")
            or rows.get("results")
            or []
        )

    if not isinstance(rows, list):
        return []

    closes: List[float] = []

    for row in rows:
        close = None

        if isinstance(row, dict):
            close = row.get("close")

        elif (
            isinstance(
                row,
                (list, tuple),
            )
            and len(row) >= 5
        ):
            close = row[4]

        try:
            c = float(close)

            if c > 0:
                closes.append(c)

        except Exception:
            pass

    return closes[-300:]


# =============================================================================
# 30-SECOND CANDLES / INDICATORS
# =============================================================================

@dataclass
class Candle30:
    bucket_ts: int
    open: float
    high: float
    low: float
    close: float


class ThirtySecondBuilder:
    def __init__(self) -> None:
        self.bucket: Optional[int] = None
        self.o: Optional[float] = None
        self.h: Optional[float] = None
        self.l: Optional[float] = None
        self.c: Optional[float] = None

    def update(
        self,
        dt: datetime,
        price: float,
    ) -> Optional[Candle30]:

        epoch = int(
            dt.timestamp()
        )

        bucket = (
            epoch
            - (
                epoch
                % CANDLE_SECONDS
            )
        )

        if self.bucket is None:
            self.bucket = bucket
            self.o = price
            self.h = price
            self.l = price
            self.c = price
            return None

        if bucket == self.bucket:
            self.h = max(
                float(self.h),
                price,
            )

            self.l = min(
                float(self.l),
                price,
            )

            self.c = price
            return None

        completed = Candle30(
            bucket_ts=int(
                self.bucket
            ),
            open=float(
                self.o
            ),
            high=float(
                self.h
            ),
            low=float(
                self.l
            ),
            close=float(
                self.c
            ),
        )

        self.bucket = bucket
        self.o = price
        self.h = price
        self.l = price
        self.c = price

        return completed


def ema(
    values: List[float],
    period: int,
) -> List[float]:

    if not values:
        return []

    alpha = (
        2.0
        / (
            period
            + 1.0
        )
    )

    out = [
        float(
            values[0]
        )
    ]

    for value in values[1:]:
        out.append(
            alpha
            * float(
                value
            )
            + (
                1.0
                - alpha
            )
            * out[-1]
        )

    return out


def rsi(
    values: List[float],
    period: int = RSI_PERIOD,
) -> Optional[float]:

    if len(values) < period + 1:
        return None

    recent = values[
        -(
            period
            + 1
        ):
    ]

    gains = 0.0
    losses = 0.0

    for a, b in zip(
        recent[:-1],
        recent[1:],
    ):
        diff = (
            b
            - a
        )

        if diff > 0:
            gains += diff
        elif diff < 0:
            losses += abs(
                diff
            )

    avg_gain = (
        gains
        / period
    )

    avg_loss = (
        losses
        / period
    )

    if avg_loss == 0:
        return 100.0

    rs = (
        avg_gain
        / avg_loss
    )

    return (
        100.0
        - (
            100.0
            / (
                1.0
                + rs
            )
        )
    )


def atr(
    candles: List[Candle30],
    period: int = ATR_PERIOD,
) -> Optional[float]:

    if len(candles) < period + 1:
        return None

    recent = candles[
        -(
            period
            + 1
        ):
    ]

    trs: List[float] = []

    for i in range(
        1,
        len(recent),
    ):
        curr = recent[i]
        prev = recent[
            i - 1
        ]

        tr = max(
            curr.high
            - curr.low,
            abs(
                curr.high
                - prev.close
            ),
            abs(
                curr.low
                - prev.close
            ),
        )

        trs.append(
            tr
        )

    return (
        sum(
            trs[-period:]
        )
        / period
    )


def adx(
    candles: List[Candle30],
    period: int = ADX_PERIOD,
) -> Optional[float]:

    if len(candles) < period * 2 + 1:
        return None

    plus_dm: List[float] = []
    minus_dm: List[float] = []
    trs: List[float] = []

    for i in range(
        1,
        len(candles),
    ):
        curr = candles[i]
        prev = candles[
            i - 1
        ]

        up = (
            curr.high
            - prev.high
        )

        down = (
            prev.low
            - curr.low
        )

        plus_dm.append(
            up
            if (
                up > down
                and up > 0
            )
            else 0.0
        )

        minus_dm.append(
            down
            if (
                down > up
                and down > 0
            )
            else 0.0
        )

        trs.append(
            max(
                curr.high
                - curr.low,
                abs(
                    curr.high
                    - prev.close
                ),
                abs(
                    curr.low
                    - prev.close
                ),
            )
        )

    dxs: List[float] = []

    for end in range(
        period,
        len(trs) + 1,
    ):
        tr_sum = sum(
            trs[
                end
                - period:
                end
            ]
        )

        if tr_sum <= 0:
            continue

        plus_di = (
            100.0
            * sum(
                plus_dm[
                    end
                    - period:
                    end
                ]
            )
            / tr_sum
        )

        minus_di = (
            100.0
            * sum(
                minus_dm[
                    end
                    - period:
                    end
                ]
            )
            / tr_sum
        )

        denom = (
            plus_di
            + minus_di
        )

        if denom <= 0:
            continue

        dxs.append(
            100.0
            * abs(
                plus_di
                - minus_di
            )
            / denom
        )

    if len(dxs) < period:
        return None

    return (
        sum(
            dxs[-period:]
        )
        / period
    )


def ema_metrics(
    closes: List[float],
) -> Dict[str, Any]:

    if len(closes) < EMA_SLOW + 3:
        return {
            "ready": False,
        }

    fast = ema(
        closes,
        EMA_FAST,
    )

    slow = ema(
        closes,
        EMA_SLOW,
    )

    f = fast[-1]
    s = slow[-1]
    prev_f = fast[-2]
    prev_s = slow[-2]

    separation_pct = (
        (
            f
            - s
        )
        / s
        * 100.0
        if s != 0
        else 0.0
    )

    fresh = None

    if (
        prev_f <= prev_s
        and f > s
    ):
        fresh = "BULLISH"

    elif (
        prev_f >= prev_s
        and f < s
    ):
        fresh = "BEARISH"

    regime = None

    if f > s:
        regime = "BULLISH"

    elif f < s:
        regime = "BEARISH"

    return {
        "ready": True,
        "ema_fast": f,
        "ema_slow": s,
        "fast_slope": (
            f
            - prev_f
        ),
        "slow_slope": (
            s
            - prev_s
        ),
        "separation_pct": separation_pct,
        "fresh": fresh,
        "regime": regime,
    }


# =============================================================================
# POSITIONBOOK / ORDERS
# =============================================================================

def positionbook() -> List[Dict[str, Any]]:
    data = post(
        "/api/v1/positionbook",
        {
            "apikey": API_KEY,
        },
    )

    rows = (
        data.get("data")
        or data.get("positions")
        or []
    )

    if isinstance(rows, dict):
        rows = (
            rows.get("positions")
            or rows.get("data")
            or []
        )

    if not isinstance(
        rows,
        list,
    ):
        return []

    return [
        row
        for row in rows
        if isinstance(
            row,
            dict,
        )
    ]


def net_qty(
    row: Dict[str, Any],
) -> int:

    for key in (
        "netqty",
        "net_qty",
        "quantity",
        "netquantity",
        "net_quantity",
        "qty",
    ):
        try:
            return int(
                float(
                    row.get(key)
                )
            )
        except Exception:
            pass

    return 0


def average_entry_price(
    row: Dict[str, Any],
) -> Optional[float]:

    for key in (
        "averageprice",
        "average_price",
        "avgprice",
        "avg_price",
        "buyavgprice",
        "buy_avg_price",
        "entry_price",
        "price",
    ):
        try:
            x = float(
                row.get(key)
            )

            if x > 0:
                return x

        except Exception:
            pass

    return None


def crude_long_positions() -> List[Dict[str, Any]]:
    result: List[
        Dict[str, Any]
    ] = []

    for row in positionbook():
        symbol = str(
            row.get("symbol")
            or ""
        ).upper()

        exchange = str(
            row.get("exchange")
            or EXCHANGE
        ).upper()

        if exchange != EXCHANGE:
            continue

        if "CRUDEOIL" not in symbol:
            continue

        if "CRUDEOILM" in symbol:
            continue

        qty = net_qty(
            row
        )

        if (
            qty > 0
            and (
                symbol.endswith(
                    "CE"
                )
                or symbol.endswith(
                    "PE"
                )
            )
        ):
            result.append(
                row
            )

    return result


def has_target_position(
    symbol: str,
) -> bool:

    target = symbol.upper()

    for row in crude_long_positions():
        if str(
            row.get("symbol")
            or ""
        ).upper() == target:
            return True

    return False


def crude_is_flat() -> bool:
    return (
        len(
            crude_long_positions()
        )
        == 0
    )


def place_market_order(
    symbol: str,
    action: str,
    quantity: int,
    product: Optional[str] = None,
) -> Dict[str, Any]:

    verify_analyzer()

    return post(
        "/api/v1/placeorder",
        {
            "apikey": API_KEY,
            "strategy": STRATEGY_NAME,
            "exchange": EXCHANGE,
            "symbol": symbol,
            "action": action.upper(),
            "quantity": int(
                quantity
            ),
            "pricetype": "MARKET",
            "product": (
                product
                or PRODUCT
            ),
        },
        timeout=ORDER_TIMEOUT,
    )


# =============================================================================
# SESSION RISK STATE
# =============================================================================

last_sell_monotonic: Optional[float] = None
last_loss_exit_monotonic: Optional[float] = None
last_loss_direction: Optional[str] = None

global_loss_pause_until: float = 0.0
consecutive_loss_exits = 0
hard_stop_count = 0
session_entries_disabled = False

# Manual/external exit state.
# This flag is informational and allows immediate reconsideration on the next
# completed 30-second decision bar. It does NOT bypass hard-stop/session locks.
manual_exit_reentry_pending = False
manual_exit_last_symbol: Optional[str] = None
manual_exit_last_direction: Optional[str] = None
manual_exit_detected_at: Optional[float] = None


def global_cooldown_remaining() -> float:
    if last_sell_monotonic is None:
        return 0.0

    return max(
        0.0,
        GLOBAL_COOLDOWN_SECONDS
        - (
            time.monotonic()
            - last_sell_monotonic
        ),
    )


def same_side_loss_cooldown_remaining(
    direction: str,
) -> float:

    if (
        last_loss_exit_monotonic is None
        or last_loss_direction != direction
    ):
        return 0.0

    return max(
        0.0,
        SAME_SIDE_LOSS_COOLDOWN_SECONDS
        - (
            time.monotonic()
            - last_loss_exit_monotonic
        ),
    )


def loss_pause_remaining() -> float:
    return max(
        0.0,
        global_loss_pause_until
        - time.monotonic(),
    )


def register_sell(
    reason: str,
    direction: Optional[str],
    pnl_pct: Optional[float],
) -> None:

    global last_sell_monotonic
    global last_loss_exit_monotonic
    global last_loss_direction
    global global_loss_pause_until
    global consecutive_loss_exits
    global hard_stop_count
    global session_entries_disabled

    last_sell_monotonic = (
        time.monotonic()
    )

    log(
        f"GLOBAL 5-MIN COOLDOWN STARTED after SELL ({reason})."
    )

    if (
        pnl_pct is not None
        and pnl_pct < 0
    ):
        consecutive_loss_exits += 1
        last_loss_exit_monotonic = (
            time.monotonic()
        )
        last_loss_direction = direction

        log(
            f"LOSS EXIT REGISTERED: pnl={pnl_pct:+.2f}% "
            f"| consecutive_losses={consecutive_loss_exits} "
            f"| same-side re-entry blocked 10 minutes."
        )

        if (
            consecutive_loss_exits
            >= CONSECUTIVE_LOSS_TRIGGER
        ):
            global_loss_pause_until = (
                time.monotonic()
                + CONSECUTIVE_LOSS_PAUSE_SECONDS
            )

            consecutive_loss_exits = 0

            log(
                "RISK PAUSE: 2 consecutive loss exits -> "
                "15-minute global no-entry period."
            )

    elif (
        pnl_pct is not None
        and pnl_pct >= 0
    ):
        consecutive_loss_exits = 0

    if reason == "HARD_STOP_5PCT":
        hard_stop_count += 1

        log(
            f"HARD STOP COUNT={hard_stop_count}/"
            f"{MAX_HARD_STOPS_PER_SESSION}"
        )

        if (
            hard_stop_count
            >= MAX_HARD_STOPS_PER_SESSION
        ):
            session_entries_disabled = True

            log(
                "SESSION RISK LOCK: maximum hard stops reached. "
                "No more NEW entries this script session."
            )


def square_off_all_crude(
    reason: str,
    direction: Optional[str] = None,
    pnl_pct: Optional[float] = None,
) -> bool:

    positions = crude_long_positions()

    if not positions:
        return True

    any_sell = False

    for row in positions:
        symbol = str(
            row.get("symbol")
            or ""
        ).upper()

        qty = net_qty(
            row
        )

        product = str(
            row.get("product")
            or row.get("producttype")
            or PRODUCT
        ).upper()

        if qty <= 0:
            continue

        log(
            f"SQUARE-OFF {reason}: SELL {symbol} qty={qty} MARKET"
        )

        response = place_market_order(
            symbol=symbol,
            action="SELL",
            quantity=qty,
            product=product,
        )

        log(
            f"SANDBOX SELL {symbol}: {response}"
        )

        any_sell = True

    if any_sell:
        register_sell(
            reason,
            direction,
            pnl_pct,
        )

    time.sleep(
        1.0
    )

    remaining = crude_long_positions()

    if remaining:
        log(
            "POSITIONBOOK NOT FLAT after square-off."
        )
        return False

    log(
        f"POSITIONBOOK VERIFIED FLAT after {reason}."
    )

    return True


def dynamic_quantity(
    symbol: str,
    rows: List[Dict[str, Any]],
) -> Tuple[
    int,
    float,
    int,
    int,
]:

    option_price = ltp(
        symbol
    )

    lot_size = lot_size_for_symbol(
        rows,
        symbol,
    )

    one_lot_cost = (
        option_price
        * lot_size
    )

    if one_lot_cost <= 0:
        raise OpenAlgoError(
            f"Invalid lot cost for {symbol}."
        )

    lots = int(
        CAPITAL_RUPEES
        // one_lot_cost
    )

    if lots < 1:
        return (
            0,
            option_price,
            lot_size,
            0,
        )

    qty = (
        lots
        * lot_size
    )

    return (
        qty,
        option_price,
        lot_size,
        lots,
    )


# =============================================================================
# MANAGED POSITION
# =============================================================================

@dataclass
class ManagedPosition:
    symbol: str
    direction: str
    quantity: int
    entry_price: float
    peak_pnl_pct: float = 0.0
    profit_lock_active: bool = False
    profit_floor_pct: float = 0.0


def infer_managed_position() -> Optional[ManagedPosition]:

    for row in crude_long_positions():
        symbol = str(
            row.get("symbol")
            or ""
        ).upper()

        if not (
            symbol.endswith("CE")
            or symbol.endswith("PE")
        ):
            continue

        entry = average_entry_price(
            row
        )

        if entry is None:
            log(
                f"POSITION TRACK WARNING: no average entry for {symbol}."
            )
            return None

        return ManagedPosition(
            symbol=symbol,
            direction=(
                "BULLISH"
                if symbol.endswith("CE")
                else "BEARISH"
            ),
            quantity=net_qty(
                row
            ),
            entry_price=entry,
            peak_pnl_pct=0.0,
        )

    return None


# =============================================================================
# ENTRY QUALITY
# =============================================================================

def candidate_option_metrics(
    direction: str,
    ce_closes: List[float],
    pe_closes: List[float],
) -> Tuple[
    Dict[str, Any],
    Dict[str, Any],
]:

    chosen = (
        ema_metrics(
            ce_closes
        )
        if direction == "BULLISH"
        else ema_metrics(
            pe_closes
        )
    )

    opposite = (
        ema_metrics(
            pe_closes
        )
        if direction == "BULLISH"
        else ema_metrics(
            ce_closes
        )
    )

    return (
        chosen,
        opposite,
    )


def future_filter_metrics(
    direction: str,
    fut_closes: List[float],
    fut_candles: List[Candle30],
) -> Dict[str, Any]:

    em = ema_metrics(
        fut_closes
    )

    if not em.get(
        "ready"
    ):
        return {
            "ready": False,
        }

    current = (
        fut_candles[-1]
        if fut_candles
        else None
    )

    current_rsi = rsi(
        fut_closes,
        RSI_PERIOD,
    )

    current_atr = atr(
        fut_candles,
        ATR_PERIOD,
    )

    current_adx = adx(
        fut_candles,
        ADX_PERIOD,
    )

    atr_pct = None

    if (
        current is not None
        and current_atr is not None
        and current.close > 0
    ):
        atr_pct = (
            current_atr
            / current.close
            * 100.0
        )

    breakout_ok = False

    if (
        len(
            fut_candles
        )
        >= BREAKOUT_LOOKBACK
        + 1
    ):
        prior = fut_candles[
            -(
                BREAKOUT_LOOKBACK
                + 1
            ):
            -1
        ]

        if direction == "BULLISH":
            breakout_ok = (
                current.close
                > max(
                    c.high
                    for c in prior
                )
            )
        else:
            breakout_ok = (
                current.close
                < min(
                    c.low
                    for c in prior
                )
            )

    if direction == "BULLISH":
        regime_ok = (
            em[
                "regime"
            ]
            == "BULLISH"
        )

        rsi_ok = (
            current_rsi is not None
            and current_rsi
            >= RSI_BULL_MIN
        )

        slope_ok = (
            em[
                "fast_slope"
            ]
            > 0
        )

        sep_ok = (
            em[
                "separation_pct"
            ]
            >= FUTURE_MIN_EMA_SEPARATION_PCT
        )

    else:
        regime_ok = (
            em[
                "regime"
            ]
            == "BEARISH"
        )

        rsi_ok = (
            current_rsi is not None
            and current_rsi
            <= RSI_BEAR_MAX
        )

        slope_ok = (
            em[
                "fast_slope"
            ]
            < 0
        )

        sep_ok = (
            em[
                "separation_pct"
            ]
            <= -FUTURE_MIN_EMA_SEPARATION_PCT
        )

    return {
        "ready": True,
        "ema": em,
        "rsi": current_rsi,
        "atr": current_atr,
        "atr_pct": atr_pct,
        "adx": current_adx,
        "regime_ok": regime_ok,
        "rsi_ok": rsi_ok,
        "slope_ok": slope_ok,
        "sep_ok": sep_ok,
        "atr_ok": (
            atr_pct is not None
            and atr_pct
            >= ATR_MIN_PCT
        ),
        "adx_ok": (
            current_adx is not None
            and current_adx
            >= ADX_MIN
        ),
        "breakout_ok": breakout_ok,
    }


def entry_quality_gate(
    direction: str,
    fut_closes: List[float],
    fut_candles: List[Candle30],
) -> bool:

    fut = future_filter_metrics(
        direction,
        fut_closes,
        fut_candles,
    )

    if not fut.get("ready"):
        log("FILTER REJECT: underlying indicator warmup incomplete.")
        return False

    future_checks = [
        fut["regime_ok"],
        fut["rsi_ok"],
        fut["slope_ok"],
        fut["sep_ok"],
        fut["atr_ok"],
        fut["adx_ok"],
        fut["breakout_ok"],
    ]

    passed = all(future_checks)

    log(
        f"UNDERLYING FILTER {direction}: "
        f"FUT_sep={fut['ema']['separation_pct']:+.3f}% "
        f"RSI={fut['rsi']} "
        f"ADX={fut['adx']} "
        f"ATR%={fut['atr_pct']} "
        f"breakout={fut['breakout_ok']} "
        f"=> {'PASS' if passed else 'REJECT'}"
    )

    return passed


def selected_option_ema_gate(
    option_closes: List[float],
    symbol: str,
) -> Tuple[bool, Dict[str, Any]]:

    m = ema_metrics(option_closes)

    if not m.get("ready"):
        log(f"OPTION FILTER REJECT {symbol}: EMA warmup incomplete.")
        return False, m

    passed = (
        m["regime"] == "BULLISH"
        and m["fast_slope"] > 0
        and m["separation_pct"] >= OPTION_MIN_EMA_SEPARATION_PCT
    )

    log(
        f"OPTION EMA FILTER {symbol}: "
        f"EMA12={m['ema_fast']:.2f} EMA41={m['ema_slow']:.2f} "
        f"| slope={m['fast_slope']:+.3f} "
        f"| separation={m['separation_pct']:+.3f}% "
        f"=> {'PASS' if passed else 'REJECT'}"
    )

    return passed, m



def preentry_live_check(
    symbol: str,
    option_ema12: float,
) -> bool:

    samples: List[float] = []

    start = time.monotonic()

    while (
        time.monotonic()
        - start
        < PREENTRY_SAMPLE_SECONDS
    ):
        try:
            samples.append(
                ltp(
                    symbol
                )
            )
        except Exception as exc:
            log(
                f"PREENTRY QUOTE ERROR {symbol}: {exc}"
            )
            return False

        time.sleep(
            0.5
        )

    if len(samples) < 2:
        return False

    first = samples[0]
    last = samples[-1]

    jump_pct = (
        (
            max(samples)
            - min(samples)
        )
        / first
        * 100.0
        if first > 0
        else 999.0
    )

    distance_from_ema_pct = (
        (
            last
            - option_ema12
        )
        / option_ema12
        * 100.0
        if option_ema12 > 0
        else 999.0
    )

    continuation_ok = (
        last
        >= first
    )

    chase_ok = (
        jump_pct
        <= MAX_PREENTRY_JUMP_PCT
        and distance_from_ema_pct
        <= MAX_OPTION_DISTANCE_FROM_EMA12_PCT
    )

    log(
        f"PREENTRY {symbol}: "
        f"{first:.2f}->{last:.2f} "
        f"| range_jump={jump_pct:.2f}% "
        f"| dist_from_EMA12={distance_from_ema_pct:.2f}% "
        f"=> continuation={continuation_ok} chase_ok={chase_ok}"
    )

    return (
        continuation_ok
        and chase_ok
    )


# =============================================================================
# ENTRY / EXIT MANAGEMENT
# =============================================================================

def option_side_for_direction(
    direction: str,
) -> str:
    return "CE" if direction == "BULLISH" else "PE"


def can_enter_direction(
    direction: str,
) -> bool:

    if session_entries_disabled:
        log(
            "ENTRY BLOCKED: session risk lock is active."
        )
        return False

    now_t = (
        now_ist()
        .time()
        .replace(
            tzinfo=None
        )
    )

    if now_t >= ENTRY_CUTOFF:
        log(
            "ENTRY BLOCKED: time cutoff reached."
        )
        return False

    global_remaining = global_cooldown_remaining()

    if global_remaining > 0:
        log(
            f"ENTRY BLOCKED: global cooldown "
            f"{global_remaining:.0f}s remaining."
        )
        return False

    loss_pause = loss_pause_remaining()

    if loss_pause > 0:
        log(
            f"ENTRY BLOCKED: consecutive-loss pause "
            f"{loss_pause:.0f}s remaining."
        )
        return False

    same_side = (
        same_side_loss_cooldown_remaining(
            direction
        )
    )

    if same_side > 0:
        log(
            f"ENTRY BLOCKED: same-side loss cooldown "
            f"{same_side:.0f}s remaining for {direction}."
        )
        return False

    return True



def manual_reentry_context(
    direction: str,
) -> bool:
    """
    Returns True when the bot is flat because a tracked position was manually
    or externally closed and the current candidate can be reconsidered.

    IMPORTANT:
    - Manual exit itself does not trigger a 5-minute cooldown.
    - All ordinary entry-quality filters remain mandatory.
    - Existing risk locks from earlier automated loss exits are NOT bypassed.
    """
    if not manual_exit_reentry_pending:
        return False

    if manual_exit_last_direction is None:
        return True

    # We allow either direction after a manual exit because the market may have
    # changed while the user was flat. Direction must still pass every filter.
    return True


def enter_direction(
    direction: str,
    rows: List[Dict[str, Any]],
    future_price: float,
    option_closes_by_symbol: Dict[str, List[float]],
    option_builders_by_symbol: Dict[str, ThirtySecondBuilder],
    option_completed_counts: Dict[str, int],
) -> Optional[ManagedPosition]:

    global manual_exit_reentry_pending
    global manual_exit_last_symbol
    global manual_exit_last_direction
    global manual_exit_detected_at

    if not can_enter_direction(direction):
        return None

    if not crude_is_flat():
        log("ENTRY ABORTED: positionbook is not flat.")
        return None

    selected_row = resolve_dynamic_option(
        rows,
        direction,
        future_price,
    )

    target = str(
        selected_row.get("symbol")
        or ""
    ).upper()

    if not target:
        log("ENTRY REJECTED: dynamic option symbol is empty.")
        return None

    # Warm selected option independently.
    if target not in option_closes_by_symbol:
        seed = history_seed_with_retry(target)

        if not seed:
            seed = fallback_live_seed(target)

        option_closes_by_symbol[target] = seed[-300:]

        option_builders_by_symbol[target] = ThirtySecondBuilder()
        option_completed_counts[target] = 0

        try:
            option_builders_by_symbol[target].update(
                now_ist(),
                ltp(target),
            )
        except Exception as exc:
            log(
                f"OPTION BUILDER PRIME WARNING {target}: {exc}"
            )

        log(
            f"SELECTED OPTION READY-CACHE {target}: "
            f"seed_closes={len(option_closes_by_symbol[target])}"
        )

    # IMPORTANT: no live LTP is appended directly to EMA.
    # We require at least one genuine completed 30-second candle for this
    # dynamically selected option before a BUY can occur.
    if option_completed_counts.get(target, 0) < 1:
        log(
            f"ENTRY WAIT {target}: need at least 1 genuine completed "
            "30-second option candle before EMA confirmation."
        )
        return None

    option_closes = option_closes_by_symbol[target]

    if len(option_closes) < MIN_EMA_READY_CLOSES:
        log(
            f"ENTRY WAIT {target}: option EMA not ready "
            f"({len(option_closes)}/{MIN_EMA_READY_CLOSES})."
        )
        return None

    option_ok, option_m = selected_option_ema_gate(
        option_closes,
        target,
    )

    if not option_ok:
        return None

    if not preentry_live_check(
        target,
        option_m["ema_fast"],
    ):
        log(
            f"ENTRY REJECTED: pre-entry live quality failed for {target}."
        )
        return None

    qty, option_price, lot_size, lots = dynamic_quantity(
        target,
        rows,
    )

    if qty <= 0:
        log(
            f"ENTRY SKIP {target}: one lot exceeds Rs.50,000 allocation."
        )
        return None

    deployment = option_price * qty

    log(
        f"DYNAMIC BUY {target} "
        f"| direction={direction} "
        f"| price={option_price:.2f} "
        f"| lot={lot_size} lots={lots} qty={qty} "
        f"| deployment=Rs.{deployment:,.0f}"
    )

    response = place_market_order(
        symbol=target,
        action="BUY",
        quantity=qty,
        product=PRODUCT,
    )

    log(f"SANDBOX BUY {target}: {response}")

    manual_exit_reentry_pending = False
    manual_exit_last_symbol = None
    manual_exit_last_direction = None
    manual_exit_detected_at = None

    time.sleep(1.0)

    return infer_managed_position()



def signal_quality_still_valid(
    managed: ManagedPosition,
    fut_closes: List[float],
    fut_candles: List[Candle30],
    managed_option_closes: List[float],
) -> bool:

    underlying_ok = entry_quality_gate(
        managed.direction,
        fut_closes,
        fut_candles,
    )

    option_ok, _ = selected_option_ema_gate(
        managed_option_closes,
        managed.symbol,
    )

    return underlying_ok and option_ok



def ladder_profit_floor(
    peak_pnl_pct: float,
) -> float:
    """
    Stepwise profit floor:
      peak < 10          -> no active floor (0.0)
      10 <= peak < 20    -> +10 floor
      20 <= peak < 25    -> +15 floor
      25 <= peak < 30    -> +20 floor
      30 <= peak < 35    -> +25 floor
      etc.

    This implements:
    - protection starts at +10%
    - +10 to +15 is fixed/protected territory
    - ladder begins once profits extend beyond that zone
    - each additional +5% peak lifts the protected floor by +5%
    """
    if peak_pnl_pct < PROFIT_LOCK_TRIGGER_PCT:
        return 0.0

    if peak_pnl_pct < (
        PROFIT_LADDER_START_PCT
        + PROFIT_LADDER_STEP_PCT
    ):
        return PROFIT_LOCK_TRIGGER_PCT

    completed_steps = math.floor(
        (
            peak_pnl_pct
            - PROFIT_LADDER_START_PCT
        )
        / PROFIT_LADDER_STEP_PCT
    )

    return max(
        PROFIT_LOCK_TRIGGER_PCT,
        PROFIT_LADDER_START_PCT
        + (
            completed_steps
            - 1
        )
        * PROFIT_LADDER_STEP_PCT,
    )


def manage_open_position(
    managed: Optional[ManagedPosition],
    fut_closes: List[float],
    fut_candles: List[Candle30],
    option_closes_by_symbol: Dict[str, List[float]],
) -> Tuple[Optional[ManagedPosition], bool]:

    global manual_exit_reentry_pending
    global manual_exit_last_symbol
    global manual_exit_last_direction
    global manual_exit_detected_at

    if managed is None:
        managed = infer_managed_position()

    if managed is None:
        return None, False

    if not has_target_position(managed.symbol):
        manual_exit_reentry_pending = True
        manual_exit_last_symbol = managed.symbol
        manual_exit_last_direction = managed.direction
        manual_exit_detected_at = time.monotonic()

        log(
            f"MANUAL/EXTERNAL EXIT DETECTED: {managed.symbol}. "
            "No new cooldown/loss count. Dynamic re-selection is allowed "
            "on the next valid 30-second decision bar."
        )

        return None, False

    try:
        current = ltp(managed.symbol)
    except Exception as exc:
        log(f"POSITION MONITOR QUOTE WARNING: {exc}")
        return managed, False

    pnl_pct = (
        (current - managed.entry_price)
        / managed.entry_price
        * 100.0
    )

    managed.peak_pnl_pct = max(
        managed.peak_pnl_pct,
        pnl_pct,
    )

    # Exact purchased option EMA uses ONLY genuine completed 30-second closes.
    managed_option_closes = option_closes_by_symbol.get(
        managed.symbol,
        [],
    )

    managed_option_m = ema_metrics(
        managed_option_closes
    )

    future_m = ema_metrics(
        fut_closes
    )

    # 1) Absolute hard stop.
    if pnl_pct <= HARD_STOP_PCT:
        log(
            f"HARD STOP -5%: {managed.symbol} "
            f"PnL={pnl_pct:+.2f}%"
        )

        square_off_all_crude(
            "HARD_STOP_5PCT",
            direction=managed.direction,
            pnl_pct=pnl_pct,
        )

        return None, True

    # 2) Purchased option own 30-sec EMA reversal.
    if (
        managed_option_m.get("ready")
        and managed_option_m["regime"] == "BEARISH"
    ):
        log(
            f"PURCHASED OPTION 30SEC EMA EXIT: {managed.symbol} "
            f"EMA12={managed_option_m['ema_fast']:.2f} "
            f"< EMA41={managed_option_m['ema_slow']:.2f}"
        )

        square_off_all_crude(
            "PURCHASED_OPTION_EMA_REVERSAL",
            direction=managed.direction,
            pnl_pct=pnl_pct,
        )

        return None, True

    # 3) Underlying/reference EMA reversal.
    if future_m.get("ready"):
        wrong_underlying = (
            managed.direction == "BULLISH"
            and future_m["regime"] == "BEARISH"
        ) or (
            managed.direction == "BEARISH"
            and future_m["regime"] == "BULLISH"
        )

        if wrong_underlying:
            log(
                f"UNDERLYING EMA REVERSAL EXIT: {managed.symbol} "
                f"| FUT regime={future_m['regime']}"
            )

            square_off_all_crude(
                "UNDERLYING_EMA_REVERSAL",
                direction=managed.direction,
                pnl_pct=pnl_pct,
            )

            return None, True

    # 4) Profit lock + ladder.
    if (
        not managed.profit_lock_active
        and managed.peak_pnl_pct >= PROFIT_LOCK_TRIGGER_PCT
    ):
        managed.profit_lock_active = True

        log(
            f"PROFIT LOCK ACTIVATED {managed.symbol}: "
            f"peak={managed.peak_pnl_pct:+.2f}% "
            f"| initial protected floor=+{PROFIT_LOCK_TRIGGER_PCT:.2f}%"
        )

    if managed.profit_lock_active:
        new_floor = ladder_profit_floor(
            managed.peak_pnl_pct
        )

        if new_floor > managed.profit_floor_pct:
            old_floor = managed.profit_floor_pct
            managed.profit_floor_pct = new_floor

            log(
                f"PROFIT LADDER STEP {managed.symbol}: "
                f"peak={managed.peak_pnl_pct:+.2f}% "
                f"| floor {old_floor:+.2f}% -> "
                f"{managed.profit_floor_pct:+.2f}%"
            )

        if pnl_pct <= managed.profit_floor_pct:
            log(
                f"PROFIT LADDER EXIT {managed.symbol}: "
                f"PnL={pnl_pct:+.2f}% <= "
                f"protected_floor={managed.profit_floor_pct:+.2f}%"
            )

            square_off_all_crude(
                "PROFIT_LADDER_EXIT",
                direction=managed.direction,
                pnl_pct=pnl_pct,
            )

            return None, True

    # 5) Loss drawdown guard.
    drawdown_from_peak = (
        managed.peak_pnl_pct
        - pnl_pct
    )

    if (
        not managed.profit_lock_active
        and pnl_pct <= LOSS_DRAWDOWN_TRIGGER_PCT
        and drawdown_from_peak >= LOSS_DRAWDOWN_FROM_PEAK_PCT
    ):
        log(
            f"LOSS DRAWDOWN EXIT {managed.symbol}: "
            f"PnL={pnl_pct:+.2f}% "
            f"peak={managed.peak_pnl_pct:+.2f}% "
            f"drawdown={drawdown_from_peak:.2f}pp"
        )

        square_off_all_crude(
            "LOSS_DRAWDOWN_EXIT",
            direction=managed.direction,
            pnl_pct=pnl_pct,
        )

        return None, True

    # 6) Soft loss + signal deterioration.
    if pnl_pct <= SOFT_LOSS_GUARD_PCT:
        if (
            len(managed_option_closes) >= MIN_EMA_READY_CLOSES
            and len(fut_closes) >= MIN_EMA_READY_CLOSES
        ):
            quality_ok = signal_quality_still_valid(
                managed,
                fut_closes,
                fut_candles,
                managed_option_closes,
            )

            if not quality_ok:
                log(
                    f"SOFT LOSS + SIGNAL FAILURE EXIT {managed.symbol}: "
                    f"PnL={pnl_pct:+.2f}%"
                )

                square_off_all_crude(
                    "SOFT_LOSS_SIGNAL_EXIT",
                    direction=managed.direction,
                    pnl_pct=pnl_pct,
                )

                return None, True

    log(
        f"POSITION {managed.symbol} "
        f"| LTP={current:.2f} ENTRY={managed.entry_price:.2f} "
        f"| PnL={pnl_pct:+.2f}% PEAK={managed.peak_pnl_pct:+.2f}% "
        f"| OPTION_30SEC_EMA={managed_option_m.get('regime')} "
        f"| FUT_EMA={future_m.get('regime')} "
        f"| PROFIT_FLOOR={managed.profit_floor_pct:+.2f}% "
        f"| HARD_STOP={HARD_STOP_PCT:.1f}%"
    )

    return managed, False



# =============================================================================
# MAIN
# =============================================================================

def main() -> int:

    require_api_key()

    log("=" * 120)
    log(
        "5PAISA CRUDEOIL DYNAMIC-OPTION V8 TRUE30SEC | EMA12/EMA41 | 30SEC | "
        "FUT REFERENCE + TRUE OPTION 30SEC EMA | Rs.50K | HARD -5% | SANDBOX"
    )
    log("=" * 120)

    force_analyzer()

    rows = search_crudeoil_rows()

    log(
        f"Search returned {len(rows)} CRUDEOIL-related MCX rows."
    )

    fut_row = nearest_active_future(
        rows
    )

    future_symbol = str(
        fut_row.get("symbol")
        or ""
    ).upper()

    log(
        f"REFERENCE UNDERLYING: {future_symbol}"
    )

    log(
        f"DYNAMIC SELECTION: nearest expiry ITM{ITM_STEPS} "
        "CE for bullish / PE for bearish."
    )

    fut_closes: List[float] = []

    # Reliable FUT warm-up.
    fut_seed = history_seed_with_retry(
        future_symbol
    )

    if not fut_seed:
        fut_seed = fallback_live_seed(
            future_symbol
        )

    fut_closes.extend(
        fut_seed[-300:]
    )

    log(
        f"FUT STARTUP SEED READY: {len(fut_closes)} values."
    )

    fut_builder = ThirtySecondBuilder()
    fut_candles: List[Candle30] = []
    fut_completed_count = 0

    try:
        fut_builder.update(
            now_ist(),
            ltp(
                future_symbol
            ),
        )
    except Exception as exc:
        log(
            f"INITIAL FUT QUOTE WARNING: {exc}"
        )

    # Every dynamic option gets its OWN 30-sec builder and EMA series.
    option_closes_by_symbol: Dict[
        str,
        List[float],
    ] = {}

    option_builders_by_symbol: Dict[
        str,
        ThirtySecondBuilder,
    ] = {}

    option_completed_counts: Dict[
        str,
        int,
    ] = {}

    managed = infer_managed_position()

    # Existing/manual position at startup:
    # warm it, create its own true 30-sec builder, and monitor independently.
    if managed is not None:
        seed = history_seed_with_retry(
            managed.symbol
        )

        if not seed:
            seed = fallback_live_seed(
                managed.symbol
            )

        option_closes_by_symbol[
            managed.symbol
        ] = seed[-300:]

        option_builders_by_symbol[
            managed.symbol
        ] = ThirtySecondBuilder()

        option_completed_counts[
            managed.symbol
        ] = 0

        try:
            option_builders_by_symbol[
                managed.symbol
            ].update(
                now_ist(),
                ltp(
                    managed.symbol
                ),
            )
        except Exception as exc:
            log(
                f"OPEN POSITION BUILDER PRIME WARNING: {exc}"
            )

        log(
            f"OPEN POSITION TRUE30SEC EMA READY {managed.symbol}: "
            f"seed={len(option_closes_by_symbol[managed.symbol])}"
        )

    direction_history: List[str] = []
    post_2329_done = False

    while True:
        now = now_ist()

        t = (
            now.time()
            .replace(
                tzinfo=None
            )
        )

        # Mandatory EOD exit.
        if t >= FORCE_EXIT_AT:
            if not post_2329_done:
                try:
                    square_off_all_crude(
                        "23_29_FORCE_EXIT"
                    )
                except Exception as exc:
                    log(
                        f"23:29 EXIT ERROR: {exc}"
                    )

                managed = None
                post_2329_done = True

            time.sleep(
                POLL_SECONDS
            )
            continue

        # --------------------------------------------------------------
        # Update currently managed option's genuine 30-sec candle stream.
        # --------------------------------------------------------------
        if managed is not None:
            if managed.symbol not in option_builders_by_symbol:
                seed = history_seed_with_retry(
                    managed.symbol
                )

                if not seed:
                    seed = fallback_live_seed(
                        managed.symbol
                    )

                option_closes_by_symbol[
                    managed.symbol
                ] = seed[-300:]

                option_builders_by_symbol[
                    managed.symbol
                ] = ThirtySecondBuilder()

                option_completed_counts[
                    managed.symbol
                ] = 0

            try:
                opt_live = ltp(
                    managed.symbol
                )

                opt_done = option_builders_by_symbol[
                    managed.symbol
                ].update(
                    now,
                    opt_live,
                )

                if opt_done is not None:
                    option_closes_by_symbol[
                        managed.symbol
                    ].append(
                        opt_done.close
                    )

                    option_closes_by_symbol[
                        managed.symbol
                    ] = option_closes_by_symbol[
                        managed.symbol
                    ][-1000:]

                    option_completed_counts[
                        managed.symbol
                    ] = (
                        option_completed_counts.get(
                            managed.symbol,
                            0,
                        )
                        + 1
                    )

                    opt_m = ema_metrics(
                        option_closes_by_symbol[
                            managed.symbol
                        ]
                    )

                    log(
                        f"OPTION 30SEC CLOSED {managed.symbol} "
                        f"| C={opt_done.close:.2f} "
                        f"| EMA12={opt_m.get('ema_fast')} "
                        f"EMA41={opt_m.get('ema_slow')} "
                        f"| regime={opt_m.get('regime')}"
                    )

            except Exception as exc:
                log(
                    f"OPTION 30SEC QUOTE WARNING {managed.symbol}: {exc}"
                )

            try:
                managed, exited = manage_open_position(
                    managed,
                    fut_closes,
                    fut_candles,
                    option_closes_by_symbol,
                )

                if exited:
                    time.sleep(
                        POLL_SECONDS
                    )
                    continue

            except Exception as exc:
                log(
                    f"POSITION MANAGEMENT WARNING: {exc}"
                )

        # --------------------------------------------------------------
        # Update reference FUT genuine 30-sec candle.
        # --------------------------------------------------------------
        try:
            fut_live = ltp(
                future_symbol
            )

            fut_done = fut_builder.update(
                now,
                fut_live,
            )

        except Exception as exc:
            log(
                f"FUT QUOTE WARNING: {exc}"
            )

            time.sleep(
                POLL_SECONDS
            )
            continue

        if fut_done is None:
            time.sleep(
                POLL_SECONDS
            )
            continue

        fut_closes.append(
            fut_done.close
        )

        fut_closes = fut_closes[
            -1000:
        ]

        fut_candles.append(
            fut_done
        )

        fut_candles = fut_candles[
            -500:
        ]

        fut_completed_count += 1

        fut_m = ema_metrics(
            fut_closes
        )

        if not fut_m.get(
            "ready"
        ):
            log(
                f"FUT EMA WARMUP: not ready "
                f"({len(fut_closes)}/{MIN_EMA_READY_CLOSES})."
            )
            continue

        # Require at least one genuine local completed 30-sec FUT candle
        # after the startup seed before any NEW entry decision.
        if fut_completed_count < 1:
            log(
                "ENTRY WAIT: no genuine completed 30-sec FUT candle yet."
            )
            continue

        direction = direction_from_future(
            fut_closes
        )

        log(
            f"30SEC FUT STATE {future_symbol} "
            f"| close={fut_done.close:.2f} "
            f"| EMA12={fut_m['ema_fast']:.2f} "
            f"EMA41={fut_m['ema_slow']:.2f} "
            f"| sep={fut_m['separation_pct']:+.3f}% "
            f"| slope={fut_m['fast_slope']:+.3f} "
            f"| direction={direction}"
        )

        if managed is not None:
            continue

        if not crude_is_flat():
            continue

        if direction is None:
            continue

        direction_history.append(
            direction
        )

        direction_history = direction_history[
            -SIGNAL_PERSIST_BARS:
        ]

        persistence_ok = (
            len(
                direction_history
            )
            >= SIGNAL_PERSIST_BARS
            and all(
                x == direction
                for x in direction_history
            )
        )

        if not persistence_ok:
            log(
                f"ENTRY WAIT: underlying {direction} not persistent for "
                f"{SIGNAL_PERSIST_BARS} bars."
            )
            continue

        if not can_enter_direction(
            direction
        ):
            continue

        # Strict data readiness: no entry without genuine FUT indicators.
        if (
            len(fut_closes)
            < MIN_EMA_READY_CLOSES
            or len(fut_candles)
            < max(
                ADX_PERIOD * 2 + 1,
                ATR_PERIOD + 1,
                BREAKOUT_LOOKBACK + 1,
            )
        ):
            log(
                f"ENTRY WAIT: FUT filter data not fully ready "
                f"(closes={len(fut_closes)}, candles={len(fut_candles)})."
            )
            continue

        if not entry_quality_gate(
            direction,
            fut_closes,
            fut_candles,
        ):
            continue

        # Resolve the current candidate in advance so its genuine 30-sec builder
        # is maintained even before the BUY.
        try:
            selected_row = resolve_dynamic_option(
                rows,
                direction,
                fut_done.close,
            )

            selected_symbol = str(
                selected_row.get("symbol")
                or ""
            ).upper()

        except Exception as exc:
            log(
                f"DYNAMIC OPTION RESOLUTION ERROR: {exc}"
            )
            continue

        if selected_symbol not in option_builders_by_symbol:
            seed = history_seed_with_retry(
                selected_symbol
            )

            if not seed:
                seed = fallback_live_seed(
                    selected_symbol
                )

            option_closes_by_symbol[
                selected_symbol
            ] = seed[-300:]

            option_builders_by_symbol[
                selected_symbol
            ] = ThirtySecondBuilder()

            option_completed_counts[
                selected_symbol
            ] = 0

            try:
                option_builders_by_symbol[
                    selected_symbol
                ].update(
                    now_ist(),
                    ltp(
                        selected_symbol
                    ),
                )
            except Exception as exc:
                log(
                    f"SELECTED OPTION PRIME WARNING {selected_symbol}: {exc}"
                )

            log(
                f"SELECTED OPTION TRACK START {selected_symbol}: "
                f"seed={len(option_closes_by_symbol[selected_symbol])}. "
                "Waiting for genuine 30-sec candle."
            )

            continue

        # Update selected flat-market candidate option builder on each FUT bar.
        try:
            selected_live = ltp(
                selected_symbol
            )

            selected_done = option_builders_by_symbol[
                selected_symbol
            ].update(
                now,
                selected_live,
            )

            if selected_done is not None:
                option_closes_by_symbol[
                    selected_symbol
                ].append(
                    selected_done.close
                )

                option_closes_by_symbol[
                    selected_symbol
                ] = option_closes_by_symbol[
                    selected_symbol
                ][-1000:]

                option_completed_counts[
                    selected_symbol
                ] = (
                    option_completed_counts.get(
                        selected_symbol,
                        0,
                    )
                    + 1
                )

                sm = ema_metrics(
                    option_closes_by_symbol[
                        selected_symbol
                    ]
                )

                log(
                    f"SELECTED OPTION 30SEC CLOSED {selected_symbol} "
                    f"| C={selected_done.close:.2f} "
                    f"| EMA12={sm.get('ema_fast')} "
                    f"EMA41={sm.get('ema_slow')} "
                    f"| regime={sm.get('regime')}"
                )

        except Exception as exc:
            log(
                f"SELECTED OPTION QUOTE WARNING {selected_symbol}: {exc}"
            )
            continue

        # Strict option readiness gate.
        if (
            option_completed_counts.get(
                selected_symbol,
                0,
            )
            < 1
        ):
            log(
                f"ENTRY WAIT {selected_symbol}: no genuine completed "
                "30-sec option candle yet."
            )
            continue

        try:
            managed = enter_direction(
                direction,
                rows,
                fut_done.close,
                option_closes_by_symbol,
                option_builders_by_symbol,
                option_completed_counts,
            )

        except Exception as exc:
            log(
                f"DYNAMIC ENTRY ERROR: {exc}"
            )

            managed = None

        time.sleep(
            POLL_SECONDS
        )




if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except KeyboardInterrupt:
        log(
            "Stopped by user. Ctrl+C does NOT automatically square off positions."
        )

    except Exception as exc:
        log(
            f"FATAL ERROR: {type(exc).__name__}: {exc}"
        )
        raise
