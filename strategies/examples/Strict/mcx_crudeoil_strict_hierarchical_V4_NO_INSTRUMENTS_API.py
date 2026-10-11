"""
OpenAlgo Strict Hierarchical Multi-Filter Options Strategy
Generated for SANDBOX / ANALYZER testing first.

Architecture:
1) Market regime: EMA9/EMA21
2) Entry trigger: EMA5/EMA9
3) VWAP
4) Market structure (HH/HL or LH/LL)
5) ADX trend strength
6) ATR volatility + no-chase
7) Momentum + acceleration
8) Breakout confirmation
9) Dynamic option selection using spread/liquidity
10) Hard stop + stepped profit lock + signal-reversal exit
11) Time-based entry cutoff and force exit

IMPORTANT:
- No strategy guarantees profit.
- Keep OpenAlgo Analyzer Mode ON until you validate logs and backtests.
- Lot size is read dynamically from the instrument master/option-chain.
"""

from __future__ import annotations
import os, sys, time, json, math, traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, time as dtime
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from openalgo import api

# -------------------- INSTANCE .ENV ONLY --------------------
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)


API_HOST = os.getenv("OPENALGO_HOST", "http://127.0.0.1:5006").strip()
WS_URL = os.getenv("OPENALGO_WS_URL", "ws://127.0.0.1:8771").strip()
API_KEY = os.getenv("OPENALGO_API_KEY", "").strip()
ALLOW_LIVE_TRADING = os.getenv("ALLOW_LIVE_TRADING", "false").lower() == "true"

if not API_KEY:
    raise RuntimeError(
        f"OPENALGO_API_KEY missing in {ENV_PATH}. "
        "Add OPENALGO_API_KEY=<your OpenAlgo app API key>"
    )

client = api(api_key=API_KEY, host=API_HOST, ws_url=WS_URL)

@dataclass
class Config:
    strategy: str
    market: str
    underlying: str
    underlying_exchange: str
    option_exchange: str
    timeframe: str
    lookback_days: int
    adx_min: float
    max_atr_extension: float
    min_ema921_gap_atr: float
    score_threshold: int
    preferred_offsets: tuple
    capital: float
    capital_per_trade: float
    hard_sl_pct: float
    profit_lock_start_pct: float
    profit_lock_step_pct: float
    entry_start: dtime
    last_entry: dtime
    force_exit: dtime
    poll_seconds: int
    product: str = "MIS"
    max_relative_spread: float = 0.015

CFG = Config(
strategy="MCX_CRUDEOIL_MULTI_FILTER_V4_RECONCILE",
market="MCX",
underlying="CRUDEOIL",
underlying_exchange="MCX",
option_exchange="MCX",
timeframe="5m",
lookback_days=5,
adx_min=20.0,
max_atr_extension=2.00,
    min_ema921_gap_atr=0.10,
score_threshold=0,
preferred_offsets=("ATM","ITM1","ITM2"),
capital=500000,
capital_per_trade=150000,
hard_sl_pct=0.05,
profit_lock_start_pct=0.20,
profit_lock_step_pct=0.05,
entry_start=dtime(9,0),
last_entry=dtime(23,25),
force_exit=dtime(23,29),
poll_seconds=10,
)

STATE_FILE = Path(__file__).with_name(f".{CFG.strategy.lower()}_state.json")
LOG_FILE = Path(__file__).with_name(
    f"{CFG.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_IST.log"
)

# -------------------- Logging --------------------
def log(msg: str):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST] {msg}"
    # Windows terminals may use CP1252; never let console encoding crash strategy.
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        safe_line = line.encode(enc, errors="replace").decode(enc, errors="replace")
        print(safe_line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# -------------------- Persistence --------------------
def load_state():
    if not STATE_FILE.exists():
        return {"position": None, "last_entry_bar": None, "armed_ce": True, "armed_pe": True}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"position": None, "last_entry_bar": None, "armed_ce": True, "armed_pe": True}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

state = load_state()

# -------------------- Indicator helpers --------------------
def ema(s, span):
    return s.ewm(span=span, adjust=False).mean()

def true_range(df):
    pc = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - pc).abs(),
        (df["low"] - pc).abs()
    ], axis=1).max(axis=1)

def atr(df, period=14):
    return true_range(df).ewm(alpha=1/period, adjust=False).mean()

def adx(df, period=14):
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    tr = true_range(df)
    atr_w = tr.ewm(alpha=1/period, adjust=False).mean().replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_w
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_w
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False).mean()

def session_vwap(df):
    # Daily reset based on exchange timestamps converted by SDK/DataFrame.
    if "datetime" in df.columns:
        dates = pd.to_datetime(df["datetime"]).dt.date
    elif isinstance(df.index, pd.DatetimeIndex):
        dates = df.index.date
    else:
        dates = pd.Series([datetime.now().date()] * len(df), index=df.index)
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].fillna(0).clip(lower=0)
    pv = typical * vol
    out = pd.Series(index=df.index, dtype=float)
    for d in pd.unique(dates):
        mask = dates == d
        vv = vol[mask].cumsum().replace(0, np.nan)
        out.loc[mask] = pv[mask].cumsum() / vv
    # Index feeds may expose zero volume. Fall back to rolling typical-price mean.
    return out.fillna(typical.rolling(20, min_periods=1).mean())

def enrich(df):
    x = df.copy()
    for c in ["open", "high", "low", "close", "volume"]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=["open","high","low","close"]).reset_index(drop=True)
    x["ema5"] = ema(x["close"], 5)
    x["ema9"] = ema(x["close"], 9)
    x["ema21"] = ema(x["close"], 21)
    x["atr14"] = atr(x, 14)
    x["adx14"] = adx(x, 14)
    x["vwap"] = session_vwap(x)
    x["gap59"] = x["ema5"] - x["ema9"]
    x["gap921"] = x["ema9"] - x["ema21"]
    return x

# -------------------- Market-data helpers --------------------
def history(symbol, exchange):
    end = datetime.now().date()
    start = end - timedelta(days=CFG.lookback_days)
    return client.history(
        symbol=symbol,
        exchange=exchange,
        interval=CFG.timeframe,
        start_date=start.strftime("%Y-%m-%d"),
        end_date=end.strftime("%Y-%m-%d"),
    )

def quote(symbol, exchange):
    r = client.quotes(symbol=symbol, exchange=exchange)
    if not isinstance(r, dict) or r.get("status") != "success":
        raise RuntimeError(f"Quote failed for {exchange}:{symbol}: {r}")
    d = r.get("data") or {}
    return {k: float(d.get(k, 0) or 0) for k in
            ["ltp","bid","ask","open","high","low","prev_close","volume","oi"]}

def parse_expiry(v):
    if pd.isna(v) or not str(v).strip():
        return None
    s = str(v).strip().upper()
    for fmt in ("%d-%b-%y", "%d-%b-%Y", "%d%b%y", "%d%b%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def nearest_index_expiry():
    r = client.expiry(symbol=CFG.underlying, exchange=CFG.option_exchange,
                      instrumenttype="options")
    if not isinstance(r, dict) or r.get("status") != "success":
        raise RuntimeError(f"Expiry lookup failed: {r}")
    today = datetime.now().date()
    vals = []
    for raw in r.get("data", []):
        d = parse_expiry(raw)
        if d and d >= today:
            vals.append(d)
    if not vals:
        raise RuntimeError(f"No current {CFG.underlying} option expiry found")
    return min(vals).strftime("%d%b%y").upper()

# -------------------- MCX dynamic contract discovery --------------------
_mcx_cache = {"at": None, "df": None, "future": None}

def _normalize_records_to_df(obj):
    """Convert common OpenAlgo/SDK response shapes into a DataFrame safely."""
    if isinstance(obj, pd.DataFrame):
        return obj.copy()

    if isinstance(obj, dict):
        # Unwrap common API wrappers recursively.
        for key in ("data", "instruments", "result", "records"):
            if key in obj:
                inner = obj.get(key)
                if inner is not None and inner is not obj:
                    try:
                        df = _normalize_records_to_df(inner)
                        if not df.empty:
                            return df
                    except Exception:
                        pass

        vals = list(obj.values())

        # Column-oriented dict.
        if vals and all(isinstance(v, (list, tuple, pd.Series, np.ndarray)) for v in vals):
            try:
                return pd.DataFrame(obj)
            except Exception:
                pass

        # Single-record scalar dict.
        if obj:
            return pd.DataFrame([obj])

        return pd.DataFrame()

    if isinstance(obj, (list, tuple)):
        if not obj:
            return pd.DataFrame()
        return pd.DataFrame(list(obj))

    return pd.DataFrame()


def mcx_instruments():
    now = datetime.now()
    if (_mcx_cache["df"] is not None and _mcx_cache["at"] and
            (now - _mcx_cache["at"]).total_seconds() < 1800):
        return _mcx_cache["df"]

    raw = client.instruments(exchange="MCX")
    df = _normalize_records_to_df(raw)

    if df.empty:
        shape = type(raw).__name__
        keys = list(raw.keys())[:20] if isinstance(raw, dict) else None
        raise RuntimeError(
            f"MCX instrument master is empty/unreadable; "
            f"response_type={shape}, keys={keys}"
        )

    # Normalize column names because SDK/API versions may vary in case.
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Normalize common aliases.
    rename_map = {}
    if "tradingsymbol" in df.columns and "symbol" not in df.columns:
        rename_map["tradingsymbol"] = "symbol"
    if "instrument_type" in df.columns and "instrumenttype" not in df.columns:
        rename_map["instrument_type"] = "instrumenttype"
    if "lot_size" in df.columns and "lotsize" not in df.columns:
        rename_map["lot_size"] = "lotsize"
    if "strike_price" in df.columns and "strike" not in df.columns:
        rename_map["strike_price"] = "strike"
    if rename_map:
        df = df.rename(columns=rename_map)

    expected_any = {"symbol", "instrumenttype", "name"}
    if not expected_any.intersection(set(df.columns)):
        raw_type = type(raw).__name__
        raw_keys = list(raw.keys())[:20] if isinstance(raw, dict) else None
        raise RuntimeError(
            "MCX instrument response does not contain instrument columns. "
            f"columns={list(df.columns)[:30]}, response_type={raw_type}, keys={raw_keys}"
        )

    log(
        f"MCX instrument master loaded: rows={len(df)} "
        f"columns={','.join(list(df.columns)[:12])}"
    )

    _mcx_cache["df"], _mcx_cache["at"] = df.copy(), now
    return df

def nearest_mcx_future():
    """
    Resolve the nearest running CRUDEOIL future without using the Instruments API.
    Uses OpenAlgo Expiry API, which supports MCX futures.
    """
    if _mcx_cache["future"]:
        return _mcx_cache["future"]

    r = client.expiry(
        symbol=CFG.underlying,
        exchange="MCX",
        instrumenttype="futures",
    )
    if not isinstance(r, dict) or r.get("status") != "success":
        raise RuntimeError(f"MCX futures expiry lookup failed: {r}")

    today = datetime.now().date()
    expiries = []
    for raw in r.get("data", []):
        d = parse_expiry(raw)
        if d and d >= today:
            expiries.append(d)

    if not expiries:
        raise RuntimeError(f"No running MCX {CFG.underlying} futures expiry found: {r}")

    exp = min(expiries)
    sym = f"{CFG.underlying}{exp.strftime('%d%b%y').upper()}FUT"
    _mcx_cache["future"] = sym
    log(f"Resolved MCX running future via expiry API: {sym}")
    return sym

# -------------------- Signal engine --------------------
def closed_bar_frame(df):
    x = enrich(df)
    if len(x) < 40:
        raise RuntimeError(f"Insufficient candles: {len(x)}")
    # Treat final row as potentially forming; use -2 as latest closed candle.
    return x


def signal_from(df):
    """
    Strict hierarchical signal:
      Mandatory gates:
        - EMA9/21 regime and slope
        - EMA5/9 trigger and expanding gap
        - VWAP alignment
        - ADX threshold
        - ATR no-chase threshold
      Confirmation:
        - At least 2 of 3: structure, breakout, acceleration
    """
    x = closed_bar_frame(df)
    b = x.iloc[-2]
    p = x.iloc[-3]
    pp = x.iloc[-4]

    bull_regime = (
        b.ema9 > b.ema21
        and b.ema9 > p.ema9
        and b.ema21 >= p.ema21
    )
    bear_regime = (
        b.ema9 < b.ema21
        and b.ema9 < p.ema9
        and b.ema21 <= p.ema21
    )

    bull_trigger = (
        b.ema5 > b.ema9
        and b.gap59 > p.gap59
        and p.gap59 >= pp.gap59
    )
    bear_trigger = (
        b.ema5 < b.ema9
        and b.gap59 < p.gap59
        and p.gap59 <= pp.gap59
    )

    bull_vwap = b.close > b.vwap
    bear_vwap = b.close < b.vwap

    adx_ok = np.isfinite(b.adx14) and b.adx14 >= CFG.adx_min

    extension = abs(b.close - b.ema9) / max(float(b.atr14), 1e-9)
    atr_ok = np.isfinite(extension) and extension <= CFG.max_atr_extension

    # V3 regime-strength filter:
    # require EMA9/EMA21 separation of at least 0.10 ATR.
    # This reduced weak/flat-regime entries in the supplied historical datasets.
    regime_gap_atr = abs(b.ema9 - b.ema21) / max(float(b.atr14), 1e-9)
    regime_gap_ok = (
        np.isfinite(regime_gap_atr)
        and regime_gap_atr >= CFG.min_ema921_gap_atr
    )

    bull_structure = (
        x.iloc[-2].high > x.iloc[-3].high > x.iloc[-4].high
        and x.iloc[-2].low > x.iloc[-3].low > x.iloc[-4].low
    )
    bear_structure = (
        x.iloc[-2].high < x.iloc[-3].high < x.iloc[-4].high
        and x.iloc[-2].low < x.iloc[-3].low < x.iloc[-4].low
    )

    bull_breakout = b.close > x.iloc[-7:-2]["high"].max()
    bear_breakout = b.close < x.iloc[-7:-2]["low"].min()

    r1 = (b.close - p.close) / max(abs(p.close), 1e-9)
    r2 = (p.close - pp.close) / max(abs(pp.close), 1e-9)
    bull_accel = r1 > 0 and r1 >= r2
    bear_accel = r1 < 0 and r1 <= r2

    bull_confirms = int(bull_structure) + int(bull_breakout) + int(bull_accel)
    bear_confirms = int(bear_structure) + int(bear_breakout) + int(bear_accel)

    bull_mandatory = (
        bull_regime and bull_trigger and bull_vwap and adx_ok and atr_ok and regime_gap_ok
    )
    bear_mandatory = (
        bear_regime and bear_trigger and bear_vwap and adx_ok and atr_ok and regime_gap_ok
    )

    bull_valid = bull_mandatory and bull_confirms >= 2
    bear_valid = bear_mandatory and bear_confirms >= 2

    direction = "CE" if bull_valid and not bear_valid else "PE" if bear_valid and not bull_valid else None
    score = (5 + bull_confirms) if direction == "CE" else (5 + bear_confirms) if direction == "PE" else 0

    # Setup reset logic: after an entry, the same direction may not re-enter
    # until EMA5 first loses its trigger relationship to EMA9.
    reset_ce = b.ema5 <= b.ema9 or b.gap59 <= p.gap59
    reset_pe = b.ema5 >= b.ema9 or b.gap59 >= p.gap59

    bar_id = str(x.iloc[-2].get("datetime", x.index[-2]))
    metrics = {
        "close": float(b.close),
        "ema5": float(b.ema5), "ema9": float(b.ema9), "ema21": float(b.ema21),
        "adx": float(b.adx14), "atr": float(b.atr14), "vwap": float(b.vwap),
        "extension_atr": float(extension),
        "regime_gap_atr": float(regime_gap_atr),
        "bull_confirms": int(bull_confirms),
        "bear_confirms": int(bear_confirms),
        "bull_valid": bool(bull_valid), "bear_valid": bool(bear_valid),
        "reset_ce": bool(reset_ce), "reset_pe": bool(reset_pe),
        "bar_id": bar_id,
    }
    return direction, score, metrics

# -------------------- Option-selection engine --------------------
def option_quality(q):
    ltp, bid, ask = q["ltp"], q["bid"], q["ask"]
    if ltp <= 0:
        return -999, None
    spread = max(0.0, ask - bid) if ask > 0 and bid > 0 else None
    rel_spread = (spread / ltp) if spread is not None else None
    if rel_spread is not None and rel_spread > CFG.max_relative_spread:
        return -999, rel_spread
    s = 0
    if rel_spread is None or rel_spread <= CFG.max_relative_spread:
        s += 1
    if q["volume"] > 0:
        s += 1
    if q["prev_close"] > 0:
        if ltp >= q["prev_close"]:
            s += 1
    return s, rel_spread

def select_index_option(option_type):
    expiry = nearest_index_expiry()
    chain = client.optionchain(
        underlying=CFG.underlying,
        exchange=CFG.underlying_exchange,
        expiry_date=expiry,
        strike_count=8,
    )
    if not isinstance(chain, dict) or chain.get("status") != "success":
        raise RuntimeError(f"Option chain failed: {chain}")
    candidates = []
    key = option_type.lower()
    for row in chain.get("chain", []):
        leg = row.get(key) or {}
        if leg.get("label") not in CFG.preferred_offsets:
            continue
        sym = leg.get("symbol")
        if not sym:
            continue
        q = {
            "ltp": float(leg.get("ltp",0) or 0),
            "bid": float(leg.get("bid",0) or 0),
            "ask": float(leg.get("ask",0) or 0),
            "volume": float(leg.get("volume",0) or 0),
            "prev_close": float(leg.get("prev_close",0) or 0),
            "oi": float(leg.get("oi",0) or 0),
            "open": float(leg.get("open",0) or 0),
            "high": float(leg.get("high",0) or 0),
            "low": float(leg.get("low",0) or 0),
        }
        qual, rel = option_quality(q)
        if qual < 0:
            continue
        candidates.append({
            "symbol": sym, "exchange": CFG.option_exchange,
            "lotsize": int(float(leg.get("lotsize",1) or 1)),
            "label": leg.get("label"), "q": q,
            "quality": qual, "rel_spread": rel if rel is not None else 999,
        })
    if not candidates:
        return None
    candidates.sort(key=lambda z: (-z["quality"], z["rel_spread"], -z["q"]["volume"]))
    return candidates[0]

def select_mcx_option(option_type):
    """
    Select a liquid ATM/ITM CRUDEOIL option using OpenAlgo optionchain().
    This avoids dependence on the failing Instruments API.
    """
    fut = nearest_mcx_future()

    # Resolve nearest running CRUDEOIL option expiry.
    er = client.expiry(
        symbol=CFG.underlying,
        exchange="MCX",
        instrumenttype="options",
    )
    if not isinstance(er, dict) or er.get("status") != "success":
        raise RuntimeError(f"MCX options expiry lookup failed: {er}")

    today = datetime.now().date()
    expiries = []
    for raw in er.get("data", []):
        d = parse_expiry(raw)
        if d and d >= today:
            expiries.append(d)

    if not expiries:
        raise RuntimeError(f"No running MCX {CFG.underlying} option expiry found: {er}")

    expiry = min(expiries).strftime("%d%b%y").upper()

    chain = client.optionchain(
        underlying=fut,
        exchange="MCX",
        expiry_date=expiry,
        strike_count=8,
    )
    if not isinstance(chain, dict) or chain.get("status") != "success":
        raise RuntimeError(f"MCX option chain failed: {chain}")

    key = option_type.lower()
    candidates = []

    # Preferred order preserves directional delta but allows a liquid alternative.
    preferred = ("ITM2", "ITM1", "ATM")

    for row in chain.get("chain", []):
        leg = row.get(key) or {}
        label = leg.get("label")
        if label not in preferred:
            continue

        sym = leg.get("symbol")
        if not sym:
            continue

        q = {
            "ltp": float(leg.get("ltp", 0) or 0),
            "bid": float(leg.get("bid", 0) or 0),
            "ask": float(leg.get("ask", 0) or 0),
            "volume": float(leg.get("volume", 0) or 0),
            "prev_close": float(leg.get("prev_close", 0) or 0),
            "oi": float(leg.get("oi", 0) or 0),
            "open": float(leg.get("open", 0) or 0),
            "high": float(leg.get("high", 0) or 0),
            "low": float(leg.get("low", 0) or 0),
        }

        qual, rel = option_quality(q)
        if qual < 0:
            continue

        try:
            lotsize = int(float(leg.get("lotsize", 1) or 1))
        except Exception:
            lotsize = 1

        candidates.append({
            "symbol": sym,
            "exchange": "MCX",
            "lotsize": lotsize,
            "label": label,
            "q": q,
            "quality": qual,
            "rel_spread": rel if rel is not None else 999,
            "preference_rank": preferred.index(label),
        })

    if not candidates:
        log(
            f"No acceptable MCX {option_type} candidate from option chain "
            f"for future={fut}, expiry={expiry}"
        )
        return None

    candidates.sort(
        key=lambda z: (
            z["preference_rank"],
            -z["quality"],
            z["rel_spread"],
            -z["q"]["volume"],
        )
    )

    chosen = candidates[0]
    log(
        f"MCX selected {chosen['symbol']} label={chosen['label']} "
        f"lot={chosen['lotsize']} quality={chosen['quality']}"
    )
    return chosen

def select_option(option_type):
    return select_mcx_option(option_type) if CFG.market == "MCX" else select_index_option(option_type)


# -------------------- V4 broker reconciliation / square-off safety --------------------
def actual_open_qty(symbol, exchange):
    """Return strategy-level open quantity for this exact symbol; None if status is unknown."""
    try:
        r = client.openposition(
            strategy=CFG.strategy,
            symbol=symbol,
            exchange=exchange,
            product=CFG.product,
        )
        if isinstance(r, dict) and r.get("status") == "success":
            return int(float(r.get("quantity", 0) or 0))
        log(f"OPENPOSITION unavailable for {exchange}:{symbol}: {r}")
    except Exception as e:
        log(f"OPENPOSITION error for {exchange}:{symbol}: {e}")
    return None


def reconcile_tracked_position():
    """
    Reconcile local state with OpenAlgo/broker state every loop.
    Manual exit: local position exists but actual strategy quantity is zero -> clear local state.
    Quantity mismatch: synchronize tracked quantity downward/upward to actual quantity.
    This does NOT alter signal generation.
    """
    pos = state.get("position")
    if not pos:
        return True

    actual = actual_open_qty(pos["symbol"], pos["exchange"])
    if actual is None:
        # Unknown is not treated as flat. Fail safe and keep local state.
        return False

    if actual == 0:
        log(f"MANUAL/EXTERNAL EXIT DETECTED: {pos['symbol']} is flat at broker/OpenAlgo. Clearing local state.")
        old_type = pos.get("option_type")
        state["position"] = None
        # Do not immediately re-enter the exact same stale setup after a manual exit.
        # A normal EMA5/EMA9 trigger reset will re-arm it, preserving V3 signal quality.
        if old_type == "CE":
            state["armed_ce"] = False
        elif old_type == "PE":
            state["armed_pe"] = False
        save_state(state)
        return True

    if abs(actual) != int(pos.get("qty", 0)):
        log(f"POSITION QTY RECONCILE {pos['symbol']}: local={pos.get('qty')} actual={actual}")
        pos["qty"] = abs(actual)
        state["position"] = pos
        save_state(state)
    return True


def wait_until_flat(symbol, exchange, timeout_seconds=12, poll=1.0):
    """Confirm actual strategy position is flat before allowing an opposite/new position."""
    deadline = time.time() + timeout_seconds
    last = None
    while time.time() < deadline:
        last = actual_open_qty(symbol, exchange)
        if last == 0:
            return True
        if last is None:
            time.sleep(poll)
            continue
        time.sleep(poll)
    log(f"FLAT CONFIRMATION TIMEOUT {exchange}:{symbol}; last_qty={last}")
    return False


def cancel_strategy_orders():
    try:
        r = client.cancelallorder(strategy=CFG.strategy)
        if isinstance(r, dict) and r.get("status") == "success":
            log(f"Pending strategy orders cancelled: {r.get('message', 'success')}")
            return True
        log(f"Cancel-all returned: {r}")
    except Exception as e:
        log(f"Cancel-all error: {e}")
    return False


def strategy_failsafe_close(reason):
    """End-of-day/shutdown failsafe: cancel pending orders and ask OpenAlgo to close strategy positions."""
    cancel_strategy_orders()
    try:
        r = client.closeposition(strategy=CFG.strategy)
        log(f"STRATEGY CLOSEPOSITION ({reason}): {r}")
        return isinstance(r, dict) and r.get("status") == "success"
    except Exception as e:
        log(f"STRATEGY CLOSEPOSITION error ({reason}): {e}")
        return False

# -------------------- Quantity / orders --------------------
def dynamic_quantity(ltp, lot_size):
    if ltp <= 0 or lot_size <= 0:
        return 0
    budget = min(CFG.capital, CFG.capital_per_trade)
    one_lot = ltp * lot_size
    lots = max(0, int(budget // one_lot))
    return lots * lot_size

def analyzer_mode_on():
    try:
        r = client.analyzerstatus()
        text = json.dumps(r).lower()
        return ("true" in text or "analyze" in text or '"mode": "analyzer"' in text
                or '"mode":"analyzer"' in text)
    except Exception:
        return False

def order_allowed():
    if ALLOW_LIVE_TRADING:
        return True
    if analyzer_mode_on():
        return True
    log("ORDER BLOCKED: Analyzer Mode not confirmed and ALLOW_LIVE_TRADING=false.")
    return False

def executed_price(order_id, fallback_symbol, fallback_exchange):
    if order_id:
        for _ in range(4):
            try:
                time.sleep(1)
                r = client.orderstatus(order_id=order_id, strategy=CFG.strategy)
                if isinstance(r, dict) and r.get("status") == "success":
                    d = r.get("data", {})
                    px = float(d.get("average_price", 0) or 0)
                    if px > 0:
                        return px
            except Exception:
                pass
    return quote(fallback_symbol, fallback_exchange)["ltp"]

def place_buy(opt):
    qty = dynamic_quantity(opt["q"]["ltp"], opt["lotsize"])
    if qty <= 0:
        log(f"SKIP: budget cannot buy one lot of {opt['symbol']}")
        return False
    if not order_allowed():
        return False
    r = client.placeorder(
        strategy=CFG.strategy,
        symbol=opt["symbol"],
        action="BUY",
        exchange=opt["exchange"],
        price_type="MARKET",
        product=CFG.product,
        quantity=qty,
    )
    if not isinstance(r, dict) or r.get("status") != "success":
        log(f"ENTRY ORDER FAILED: {r}")
        return False
    px = executed_price(r.get("orderid"), opt["symbol"], opt["exchange"])
    pos = {
        "symbol": opt["symbol"], "exchange": opt["exchange"],
        "option_type": "CE" if opt["symbol"].upper().endswith("CE") else "PE",
        "qty": qty, "entry": px, "lotsize": opt["lotsize"],
        "hard_stop": px * (1 - CFG.hard_sl_pct),
        "max_ltp": px, "lock_price": None,
        "entered_at": datetime.now().isoformat(),
    }
    state["position"] = pos
    save_state(state)
    log(f"BUY {opt['symbol']} qty={qty} @ ~{px:.2f} | SL={pos['hard_stop']:.2f}")
    return True

def exit_position(reason):
    pos = state.get("position")
    if not pos:
        return True
    if not order_allowed():
        log(f"EXIT REQUIRED but order blocked: {reason}")
        return False

    # Reconcile immediately before exit. If user already exited manually, do not send a new SELL.
    actual = actual_open_qty(pos["symbol"], pos["exchange"])
    if actual == 0:
        log(f"EXIT SKIPPED ({reason}): {pos['symbol']} already flat (manual/external exit).")
        state["position"] = None
        save_state(state)
        return True
    if actual is None:
        log(f"EXIT DEFERRED ({reason}): could not confirm actual broker quantity.")
        return False

    qty_to_close = abs(int(actual))
    if qty_to_close <= 0:
        return False

    # For the long-option architecture, positive actual qty is closed with SELL.
    # If a negative quantity is ever detected, BUY it back rather than increasing the short.
    action = "SELL" if actual > 0 else "BUY"
    r = client.placeorder(
        strategy=CFG.strategy,
        symbol=pos["symbol"],
        action=action,
        exchange=pos["exchange"],
        price_type="MARKET",
        product=CFG.product,
        quantity=qty_to_close,
    )
    if not isinstance(r, dict) or r.get("status") != "success":
        log(f"EXIT ORDER FAILED ({reason}): {r}")
        return False

    px = executed_price(r.get("orderid"), pos["symbol"], pos["exchange"])
    # Do not clear state until OpenAlgo/broker confirms flat.
    if not wait_until_flat(pos["symbol"], pos["exchange"]):
        log(f"EXIT SENT but NOT YET CONFIRMED FLAT ({reason}); local state retained.")
        return False

    # P&L display assumes original architecture is long options.
    pnl = (px - float(pos["entry"])) * int(pos["qty"])
    pct = (px / float(pos["entry"]) - 1) * 100 if float(pos["entry"]) else 0.0
    log(f"EXIT {pos['symbol']} @ ~{px:.2f} | {reason} | P&L approx Rs {pnl:.2f} ({pct:+.2f}%) | FLAT CONFIRMED")
    state["position"] = None
    save_state(state)
    return True

# -------------------- Position manager --------------------
def manage_position(underlying_direction=None, underlying_score=0):
    pos = state.get("position")
    if not pos:
        return
    try:
        q = quote(pos["symbol"], pos["exchange"])
        ltp = q["ltp"]
        entry = float(pos["entry"])
        pos["max_ltp"] = max(float(pos.get("max_ltp", entry)), ltp)

        # Hard stop
        if ltp <= float(pos["hard_stop"]):
            state["position"] = pos; save_state(state)
            exit_position("HARD STOP")
            return

        # Stepped profit lock:
        # at +20%, lock +15%; each extra +5% raises the lock by +5%.
        max_gain = pos["max_ltp"] / entry - 1
        start = CFG.profit_lock_start_pct
        step = CFG.profit_lock_step_pct
        if max_gain >= start:
            steps = math.floor((max_gain - start) / step)
            locked_gain = max(0.0, start - step + steps * step)
            pos["lock_price"] = entry * (1 + locked_gain)
            if ltp <= pos["lock_price"]:
                state["position"] = pos; save_state(state)
                exit_position(f"PROFIT LOCK ({locked_gain*100:.0f}% floor)")
                return

        # Directional reversal: only exit when opposite signal is reasonably strong.
        if underlying_direction and underlying_score >= max(7, CFG.score_threshold - 3):
            if pos["option_type"] != underlying_direction:
                state["position"] = pos; save_state(state)
                exit_position("UNDERLYING REGIME REVERSAL")
                return

        state["position"] = pos
        save_state(state)
        gain = (ltp / entry - 1) * 100
        lock_txt = f"{pos['lock_price']:.2f}" if pos.get("lock_price") else "-"
        log(f"MONITOR {pos['symbol']} LTP={ltp:.2f} P&L={gain:+.2f}% "
            f"MAX={pos['max_ltp']:.2f} LOCK={lock_txt}")
    except Exception as e:
        log(f"Position monitor error: {e}")

# -------------------- Trading clock --------------------
def now_t():
    return datetime.now().time().replace(microsecond=0)

def entry_window():
    t = now_t()
    return CFG.entry_start <= t < CFG.last_entry

def force_exit_due():
    return now_t() >= CFG.force_exit

# -------------------- Main loop --------------------
def underlying_contract():
    if CFG.market == "MCX":
        return nearest_mcx_future(), "MCX"
    return CFG.underlying, CFG.underlying_exchange

def main():
    log("=" * 80)
    log(f"START {CFG.strategy} | market={CFG.market} timeframe={CFG.timeframe}")
    log(f"Capital=Rs {CFG.capital:,.0f} | per-trade cap=Rs {CFG.capital_per_trade:,.0f}")
    log(f"EMA regime 9/21 + trigger 5/9 | ADX>={CFG.adx_min} | "
        f"ATR extension<={CFG.max_atr_extension}")
    log(f"Safe gate: ALLOW_LIVE_TRADING={ALLOW_LIVE_TRADING}; Analyzer Mode is accepted.")
    log("=" * 80)

    while True:
        try:
            if force_exit_due():
                # No new entries after force-exit time. Cancel pending orders first.
                cancel_strategy_orders()
                reconcile_tracked_position()
                if state.get("position"):
                    exit_position("FORCE EXIT TIME")
                # Failsafe in case a strategy position exists that local state missed.
                strategy_failsafe_close("FORCE EXIT TIME")
                reconcile_tracked_position()
                time.sleep(max(5, CFG.poll_seconds))
                continue

            sym, exch = underlying_contract()
            df = history(sym, exch)
            direction, score, m = signal_from(df)

            # Rearm a direction only after its fast trigger has reset.
            if m.get("reset_ce"):
                state["armed_ce"] = True
            if m.get("reset_pe"):
                state["armed_pe"] = True
            save_state(state)

            log(
                f"{sym} close={m['close']:.2f} E5={m['ema5']:.2f} "
                f"E9={m['ema9']:.2f} E21={m['ema21']:.2f} "
                f"ADX={m['adx']:.1f} ATR={m['atr']:.2f} VWAP={m['vwap']:.2f} "
                f"ext={m['extension_atr']:.2f}ATR gap921={m['regime_gap_atr']:.2f}ATR "
                f"confirm CE/PE={m['bull_confirms']}/{m['bear_confirms']} "
                f"armed CE/PE={state.get('armed_ce', True)}/{state.get('armed_pe', True)} "
                f"dir={direction}"
            )

            # V4 safety: reconcile broker/OpenAlgo state before managing or entering.
            reconcile_tracked_position()

            # Manage existing position first. V3 signal logic is unchanged.
            manage_position(direction, score)

            if state.get("position"):
                time.sleep(CFG.poll_seconds)
                continue

            if not entry_window():
                time.sleep(CFG.poll_seconds)
                continue

            if not direction:
                time.sleep(CFG.poll_seconds)
                continue

            # One entry per setup. Same-direction re-entry needs a trigger reset first.
            if direction == "CE" and not state.get("armed_ce", True):
                time.sleep(CFG.poll_seconds)
                continue
            if direction == "PE" and not state.get("armed_pe", True):
                time.sleep(CFG.poll_seconds)
                continue

            # Prevent repeated entry on the same completed bar.
            if state.get("last_entry_bar") == m["bar_id"]:
                time.sleep(CFG.poll_seconds)
                continue

            opt = select_option(direction)
            if not opt:
                log("No acceptable liquid option candidate found.")
                time.sleep(CFG.poll_seconds)
                continue

            # Add up to 3 points from option quality to the underlying score.
            total_score = score + int(opt["quality"])
            rel = opt["rel_spread"]
            spread_txt = "n/a" if rel == 999 else f"{rel*100:.2f}%"
            log(
                f"CANDIDATE {opt['symbol']} {opt['label']} LTP={opt['q']['ltp']:.2f} "
                f"spread={spread_txt} vol={opt['q']['volume']:.0f} "
                f"quality={opt['quality']} total_score={total_score}"
            )

            # Threshold is on underlying; option must also pass quality >=2.
            if opt["quality"] < 2:
                log("SKIP: option quality insufficient.")
                time.sleep(CFG.poll_seconds)
                continue

            # Final V4 safety gate: reconcile once more immediately before a new BUY.
            reconcile_tracked_position()
            if state.get("position"):
                log("NEW ENTRY BLOCKED: an existing strategy position is still open/not flat-confirmed.")
                time.sleep(CFG.poll_seconds)
                continue

            if place_buy(opt):
                state["last_entry_bar"] = m["bar_id"]
                if direction == "CE":
                    state["armed_ce"] = False
                else:
                    state["armed_pe"] = False
                save_state(state)

            time.sleep(CFG.poll_seconds)

        except KeyboardInterrupt:
            log("CTRL+C received. Cancelling pending orders and reconciling before shutdown.")
            cancel_strategy_orders()
            reconcile_tracked_position()
            if state.get("position"):
                exit_position("MANUAL SHUTDOWN")
            strategy_failsafe_close("MANUAL SHUTDOWN")
            reconcile_tracked_position()
            break
        except Exception as e:
            log(f"LOOP ERROR: {e}")
            log(traceback.format_exc().splitlines()[-1])
            time.sleep(max(5, CFG.poll_seconds))

if __name__ == "__main__":
    main()
