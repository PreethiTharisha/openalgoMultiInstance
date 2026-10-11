#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NIFTY50 1-second ADAPTIVE FAST MOVE scalper VALIDATED QUALITY V7 for OpenAlgo.
Analyzer-first. Uses NORMAL / STRONG / EXPLOSIVE move classes so confirmation speed,
EMA-gap tolerance and option chase limits scale with the strength of the NIFTY impulse.
"""
from __future__ import annotations
import os, time, statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime, date, time as dt_time
from typing import Deque, Optional, Tuple
from zoneinfo import ZoneInfo
from openalgo import api

IST = ZoneInfo('Asia/Kolkata')
API_KEY = os.getenv('OPENALGO_API_KEY','').strip()
API_HOST = os.getenv('HOST_SERVER','http://127.0.0.1:5004').strip()
ALLOW_LIVE_TRADING = os.getenv('ALLOW_LIVE_TRADING','false').lower() == 'true'

STRATEGY_NAME='NIFTY50_1SEC_FAST_MOVE_VALIDATED_QUALITY_V7'
INDEX_SYMBOL='NIFTY'; INDEX_EXCHANGE='NSE_INDEX'; OPTIONS_EXCHANGE='NFO'; PRODUCT='MIS'; OFFSET='ITM3'

TRADING_CAPITAL_RUPEES=float(os.getenv('TRADING_CAPITAL_RUPEES','200000'))
RISK_PER_TRADE_PERCENT=float(os.getenv('RISK_PER_TRADE_PERCENT','0.25'))
MAX_CAPITAL_DEPLOYMENT_PERCENT=float(os.getenv('MAX_CAPITAL_DEPLOYMENT_PERCENT','20'))

SAMPLE_INTERVAL_SECONDS=1.0
WARMUP_SECONDS=25
NOISE_LOOKBACK_SECONDS=20
FAST_EMA_PERIOD=2; SLOW_EMA_PERIOD=5

# Fast-move impulse: require acceleration, not merely a one-off 3-second displacement
IMPULSE_WINDOW_SECONDS=3
MIN_IMPULSE_POINTS=2.5
IMPULSE_NOISE_MULT=1.8
MIN_DIRECTIONAL_MOVES=3           # at least 3 of the last 4 one-second moves
DIRECTIONAL_MOVE_LOOKBACK=4
MIN_1S_MOVE_POINTS=0.20
MIN_2S_MOVE_POINTS=0.80
ACCELERATION_TOLERANCE_POINTS=0.15  # allow tiny quote jitter while requiring cumulative expansion
MAX_NIFTY_DISTANCE_FROM_FAST_EMA=8.0
MIN_EMA_GAP_POINTS=0.15
EMA_GAP_EXPANSION_TOLERANCE=0.03

# Adaptive move classes. Stronger moves are confirmed faster and may tolerate a larger
# option premium jump because a fixed +1.5% chase ceiling rejected genuine 5-10 point NIFTY bursts.
STRONG_MOVE_POINTS=5.0
EXPLOSIVE_MOVE_POINTS=7.0

NORMAL_PULLBACK_WAIT_SECONDS=2.0
NORMAL_SIGNAL_MAX_AGE_SECONDS=5.0
NORMAL_OPTION_CHASE_CAP_PERCENT=1.75
NORMAL_OPTION_MIN_CONFIRM_PERCENT=0.15
NORMAL_EMA_KEEP_RATIO=0.90
NORMAL_MIN_IMPULSE_FOR_ENTRY_POINTS=3.0
NORMAL_MAX_RETRACE_FRACTION=0.35
NORMAL_RISK_MULTIPLIER=0.75

STRONG_PULLBACK_WAIT_SECONDS=1.25
STRONG_SIGNAL_MAX_AGE_SECONDS=4.5
STRONG_OPTION_CHASE_CAP_PERCENT=3.0
STRONG_OPTION_MIN_CONFIRM_PERCENT=-0.30
STRONG_EMA_KEEP_RATIO=0.85

EXPLOSIVE_CONTINUATION_WAIT_SECONDS=0.75
EXPLOSIVE_SIGNAL_MAX_AGE_SECONDS=6.0
EXPLOSIVE_OPTION_CHASE_CAP_PERCENT=4.0
EXPLOSIVE_10PT_CHASE_CAP_PERCENT=5.0
EXPLOSIVE_OPTION_MIN_CONFIRM_PERCENT=-0.50
EXPLOSIVE_EMA_KEEP_RATIO=0.80
EXPLOSIVE_CONTINUATION_BUFFER_POINTS=0.15

MIN_PULLBACK_POINTS=0.20
MAX_PULLBACK_FRACTION=0.45
RESUME_BUFFER_POINTS=0.20

# V6 confirmation architecture: impulse -> controlled pullback -> second impulse -> option breakout.
NORMAL_SECOND_IMPULSE_POINTS=1.25
STRONG_SECOND_IMPULSE_POINTS=1.00
EXPLOSIVE_SECOND_IMPULSE_POINTS=1.50
EXPLOSIVE_MIN_PULLBACK_POINTS=0.75
OPTION_BREAKOUT_MIN_PERCENT=0.05
FAILED_DIRECTION_COOLDOWN_SECONDS=60.0
GLOBAL_POST_TRADE_COOLDOWN_SECONDS=30.0

# V7 quality gate: default is intentionally selective. Full-day V5 showed NORMAL and
# EXPLOSIVE entries were negative overall, while STRONG was materially better.
ENABLE_NORMAL_ENTRIES=os.getenv('ENABLE_NORMAL_ENTRIES','false').lower() == 'true'
ENABLE_STRONG_ENTRIES=os.getenv('ENABLE_STRONG_ENTRIES','true').lower() == 'true'
ENABLE_EXPLOSIVE_ENTRIES=os.getenv('ENABLE_EXPLOSIVE_ENTRIES','false').lower() == 'true'
STRONG_MIN_IMPULSE_POINTS=5.5
STRONG_REQUIRED_DIRECTIONAL_MOVES=4
STRONG_MIN_CURRENT_EMA_GAP_POINTS=1.00
STRONG_MIN_PULLBACK_FRACTION=0.12
STRONG_MAX_PULLBACK_FRACTION=0.38
STRONG_SECOND_IMPULSE_POINTS=1.50
STRONG_REBREAK_BUFFER_POINTS=0.20
STRONG_OPTION_MIN_CONFIRM_PERCENT=0.20
STRONG_OPTION_CHASE_CAP_PERCENT=2.50
OPTION_BREAKOUT_MIN_PERCENT=0.10


# Fast scalp risk: protect smaller bursts sooner
# Size risk remains based on 3%, but dispatch the market exit at 2.5% to provide
# execution/slippage headroom so a nominal 3% loss is less likely to become 4%+.
HARD_STOP_PERCENT=3.0
HARD_STOP_DISPATCH_PERCENT=2.5
POSITION_MONITOR_INTERVAL_SECONDS=0.25

# Conditional soft protection below the full +2% trailing system. This is deliberately
# not a simple +1% breakeven stop: it only acts after >=1.5% peak AND momentum weakens.
SOFT_PROFIT_ARM_PERCENT=1.25
SOFT_PROFIT_FLOOR_PERCENT=0.25
SOFT_PROFIT_STEP2_ARM_PERCENT=1.50
SOFT_PROFIT_STEP2_FLOOR_PERCENT=0.50
SOFT_PROFIT_MIN_HOLD_SECONDS=3.0
NO_FOLLOW_THROUGH_SECONDS=4.0
NO_FOLLOW_THROUGH_MIN_PEAK_PERCENT=0.25
EARLY_PEAK_GIVEBACK_PERCENT=0.90
PROFIT_TRAIL_ACTIVATION_PERCENT=2.0
PROFIT_TRAIL_MIN_FLOOR_PERCENT=0.75
PROFIT_TRAIL_GIVEBACK_PERCENT=1.25
MAX_HOLD_SECONDS=75
MIN_HOLD_BEFORE_MOMENTUM_EXIT_SECONDS=8
REVERSAL_WINDOW_SECONDS=2
REVERSAL_MIN_POINTS=3.0
REVERSAL_NOISE_MULTIPLIER=1.7

ENTRY_COOLDOWN_SECONDS=12
# Zerodha/OpenAlgo MIS square-off observed at 15:15 IST. Stop new entries early enough
# for the strategy's 75-second max hold and force-flat before the broker cutoff.
MARKET_OPEN=dt_time(9,15); ENTRY_START=dt_time(9,20); ENTRY_CUTOFF=dt_time(15,12,30); FORCE_CLOSE=dt_time(15,14,0); FINAL_SWEEP=dt_time(15,25,0); MARKET_CLOSE=dt_time(15,30)
ORDER_FILL_TIMEOUT_SECONDS=8.0; ORDER_STATUS_POLL_SECONDS=0.20

# Market-data sanity guard. A single implausible one-second NIFTY jump is NOT fed into
# EMA/impulse logic. Two consecutive quotes near the new level confirm a genuine regime
# shift, clear the old buffer, and force a fresh warm-up before new entries.
MAX_VALID_1S_SPOT_JUMP_POINTS=40.0
DISCONTINUITY_CONFIRM_TOLERANCE_POINTS=10.0
DISCONTINUITY_CONFIRM_SAMPLES=2

# ITM3 NIFTY options should not have near-zero/absurd LTPs. This also blocks malformed
# option quotes such as the sub-rupee readings seen during the late-session feed anomaly.
MIN_REASONABLE_OPTION_LTP=5.0
MAX_REASONABLE_OPTION_LTP=5000.0

@dataclass
class Tick:
    t: float
    price: float

@dataclass
class Signal:
    direction: str
    move_class: str
    armed_at: float
    start_price: float
    impulse_price: float
    impulse_points: float
    symbol: str
    exchange: str
    option_type: str
    lot_size: int
    option_ref_ltp: float
    pullback_extreme: float
    pullback_wait_seconds: float
    max_age_seconds: float
    option_chase_cap_percent: float
    option_min_confirm_percent: float
    ema_keep_ratio: float
    saw_pullback: bool=False
    option_highest_ltp: float=0.0

@dataclass
class Position:
    symbol: str
    exchange: str
    option_type: str
    move_class: str
    quantity: int
    entry_price: float
    entry_monotonic: float
    hard_stop: float
    peak_pnl_pct: float=0.0
    trailing_active: bool=False
    trailing_floor_pct: float=0.0
    last_status_log_monotonic: float=0.0
    entry_order_id: str=''

class Scalper:
    def __init__(self):
        if not API_KEY: raise RuntimeError('OPENALGO_API_KEY is not configured')
        self.client=api(api_key=API_KEY, host=API_HOST)
        self.ticks:Deque[Tick]=deque(maxlen=240)
        self.signal:Optional[Signal]=None
        self.position:Optional[Position]=None
        self.daily_trade_count=0
        self.last_entry_monotonic=0.0
        self.current_day=self.now().date()
        self.expiry_cache_date:Optional[date]=None
        self.expiry_cache_value:Optional[str]=None
        self.analyze_mode=True
        self.discontinuity_candidate:Optional[float]=None
        self.discontinuity_confirm_count=0
        self.completed_trades=[]
        self.last_failed_direction_monotonic={'BULLISH':-1e9,'BEARISH':-1e9}
        self.final_sweep_done=False
        self._verify_mode()

    @staticmethod
    def now(): return datetime.now(IST)
    def log(self,msg): print(f"[{self.now().strftime('%Y-%m-%d %H:%M:%S')} IST] {msg}",flush=True)

    def _verify_mode(self):
        r=self.client.analyzerstatus()
        if r.get('status')!='success': raise RuntimeError(str(r))
        d=r.get('data',{})
        self.analyze_mode=bool(d.get('analyze_mode'))
        self.log(f"OpenAlgo mode={d.get('mode','unknown')} (analyze_mode={self.analyze_mode})")
        if not self.analyze_mode and not ALLOW_LIVE_TRADING:
            raise RuntimeError('LIVE mode detected but ALLOW_LIVE_TRADING=false. Use Analyzer first.')

    def _roll_day(self):
        d=self.now().date()
        if d!=self.current_day:
            self.current_day=d; self.daily_trade_count=0; self.signal=None
            self.expiry_cache_date=None; self.expiry_cache_value=None; self.final_sweep_done=False
            self.log('New trading day: counters reset.')

    def _quote(self,symbol,exchange):
        try:
            r=self.client.quotes(symbol=symbol,exchange=exchange)
            if r.get('status')!='success': return None
            x=float(r.get('data',{}).get('ltp') or 0)
            return x if x>0 else None
        except Exception: return None

    @staticmethod
    def _option_ltp_sane(x):
        return x is not None and MIN_REASONABLE_OPTION_LTP <= x <= MAX_REASONABLE_OPTION_LTP

    def _spot_tick_is_usable(self,spot):
        if not self.ticks:
            self.discontinuity_candidate=None; self.discontinuity_confirm_count=0
            return True
        prev=self.ticks[-1].price
        gap=abs(spot-prev)
        if self.discontinuity_candidate is None:
            if gap<=MAX_VALID_1S_SPOT_JUMP_POINTS:
                return True
            self.discontinuity_candidate=spot; self.discontinuity_confirm_count=1
            self.signal=None
            self.log(f'DATA GUARD: suspicious NIFTY 1s jump {prev:.2f}->{spot:.2f} ({spot-prev:+.2f}pt); tick quarantined, awaiting confirmation')
            return False

        cand=self.discontinuity_candidate
        if abs(spot-prev)<=MAX_VALID_1S_SPOT_JUMP_POINTS:
            self.log(f'DATA GUARD: feed returned to prior regime at {spot:.2f}; quarantined jump discarded')
            self.discontinuity_candidate=None; self.discontinuity_confirm_count=0
            return True
        if abs(spot-cand)<=DISCONTINUITY_CONFIRM_TOLERANCE_POINTS:
            self.discontinuity_confirm_count+=1
            self.discontinuity_candidate=spot
            if self.discontinuity_confirm_count>=DISCONTINUITY_CONFIRM_SAMPLES:
                self.log(f'DATA GUARD: new NIFTY level confirmed near {spot:.2f}; clearing signal history and restarting {WARMUP_SECONDS}s warm-up')
                self.ticks.clear(); self.signal=None
                self.discontinuity_candidate=None; self.discontinuity_confirm_count=0
                return True
            return False
        self.log(f'DATA GUARD: unstable discontinuity candidate {cand:.2f}->{spot:.2f}; still quarantining')
        self.discontinuity_candidate=spot; self.discontinuity_confirm_count=1
        self.signal=None
        return False

    @staticmethod
    def _ema(vals,period):
        if not vals: return 0.0
        a=2/(period+1); out=vals[0]
        for x in vals[1:]: out=a*x+(1-a)*out
        return out

    def _recent_prices(self,seconds):
        if not self.ticks: return []
        cutoff=self.ticks[-1].t-seconds
        return [x.price for x in self.ticks if x.t>=cutoff]

    def _price_ago(self,seconds):
        if not self.ticks: return None
        target=self.ticks[-1].t-seconds; c=None
        for x in self.ticks:
            if x.t<=target: c=x.price
            else: break
        return c

    def _noise(self):
        p=self._recent_prices(NOISE_LOOKBACK_SECONDS)
        if len(p)<8: return 0.0
        m=[abs(p[i]-p[i-1]) for i in range(1,len(p))]
        return statistics.median(m) if m else 0.0

    def _dir_count(self,n=4):
        p=list(self.ticks)[-(n+1):]
        if len(p)<n+1: return 0,0
        m=[p[i].price-p[i-1].price for i in range(1,len(p))]
        return sum(x>0 for x in m),sum(x<0 for x in m)

    def _ema_gap_series(self,lookback_prices=10):
        vals=[x.price for x in list(self.ticks)[-lookback_prices:]]
        if len(vals)<6:return None
        gaps=[]
        # Calculate EMA2-EMA5 on three successive snapshots ending 2s ago, 1s ago, now.
        for cut in (2,1,0):
            v=vals[:-cut] if cut else vals
            if len(v)<5:return None
            gaps.append(self._ema(v,FAST_EMA_PERIOD)-self._ema(v,SLOW_EMA_PERIOD))
        return gaps[0],gaps[1],gaps[2]

    @staticmethod
    def _move_profile(impulse_points):
        mag=abs(impulse_points)
        if mag>=EXPLOSIVE_MOVE_POINTS:
            chase=EXPLOSIVE_10PT_CHASE_CAP_PERCENT if mag>=10.0 else EXPLOSIVE_OPTION_CHASE_CAP_PERCENT
            return ('EXPLOSIVE',EXPLOSIVE_CONTINUATION_WAIT_SECONDS,EXPLOSIVE_SIGNAL_MAX_AGE_SECONDS,
                    chase,EXPLOSIVE_OPTION_MIN_CONFIRM_PERCENT,EXPLOSIVE_EMA_KEEP_RATIO)
        if mag>=STRONG_MOVE_POINTS:
            return ('STRONG',STRONG_PULLBACK_WAIT_SECONDS,STRONG_SIGNAL_MAX_AGE_SECONDS,
                    STRONG_OPTION_CHASE_CAP_PERCENT,STRONG_OPTION_MIN_CONFIRM_PERCENT,STRONG_EMA_KEEP_RATIO)
        return ('NORMAL',NORMAL_PULLBACK_WAIT_SECONDS,NORMAL_SIGNAL_MAX_AGE_SECONDS,
                NORMAL_OPTION_CHASE_CAP_PERCENT,NORMAL_OPTION_MIN_CONFIRM_PERCENT,NORMAL_EMA_KEEP_RATIO)

    @staticmethod
    def _ema_gap_holds(direction,gaps,keep_ratio):
        g2,g1,g0=gaps
        a2,a1,a0=abs(g2),abs(g1),abs(g0)
        if direction=='BULLISH':
            if g0<=0 or a0<MIN_EMA_GAP_POINTS:return False
        else:
            if g0>=0 or a0<MIN_EMA_GAP_POINTS:return False
        # Do not demand perfect second-by-second monotonic expansion. Current momentum may
        # contract slightly, but it must retain most of the immediately prior gap and must
        # not collapse versus two samples ago.
        return a0>=a1*keep_ratio and a0>=a2*keep_ratio

    def _acceleration_state(self):
        cur=self.ticks[-1].price
        p1=self._price_ago(1); p2=self._price_ago(2); p3=self._price_ago(3)
        if None in (p1,p2,p3):return None
        m1=cur-p1; m2=cur-p2; m3=cur-p3
        up,down=self._dir_count(DIRECTIONAL_MOVE_LOOKBACK)
        gaps=self._ema_gap_series()
        if gaps is None:return None
        g2,g1,g0=gaps
        bullish_accel=(m1>=MIN_1S_MOVE_POINTS and m2>=MIN_2S_MOVE_POINTS and
                       m3>=MIN_IMPULSE_POINTS and
                       m2+ACCELERATION_TOLERANCE_POINTS>=m1 and
                       m3+ACCELERATION_TOLERANCE_POINTS>=m2 and
                       up>=MIN_DIRECTIONAL_MOVES)
        bearish_accel=(m1<=-MIN_1S_MOVE_POINTS and m2<=-MIN_2S_MOVE_POINTS and
                       m3<=-MIN_IMPULSE_POINTS and
                       abs(m2)+ACCELERATION_TOLERANCE_POINTS>=abs(m1) and
                       abs(m3)+ACCELERATION_TOLERANCE_POINTS>=abs(m2) and
                       down>=MIN_DIRECTIONAL_MOVES)
        bullish_gap=(g0>=MIN_EMA_GAP_POINTS and
                     g0+EMA_GAP_EXPANSION_TOLERANCE>=g1 and
                     g1+EMA_GAP_EXPANSION_TOLERANCE>=g2 and g0>0)
        bearish_gap=(g0<=-MIN_EMA_GAP_POINTS and
                     abs(g0)+EMA_GAP_EXPANSION_TOLERANCE>=abs(g1) and
                     abs(g1)+EMA_GAP_EXPANSION_TOLERANCE>=abs(g2) and g0<0)
        return m1,m2,m3,up,down,(g2,g1,g0),bullish_accel,bearish_accel,bullish_gap,bearish_gap

    @staticmethod
    def _parse_expiry(raw):
        for fmt in ('%d-%b-%y','%d%b%y','%d-%b-%Y','%d%b%Y'):
            try:return datetime.strptime(str(raw).strip().upper(),fmt).date()
            except ValueError:pass
        return None

    def _nearest_expiry(self):
        today=self.now().date()
        if self.expiry_cache_date==today and self.expiry_cache_value:return self.expiry_cache_value
        r=self.client.expiry(symbol=INDEX_SYMBOL,exchange=OPTIONS_EXCHANGE,instrumenttype='options')
        if r.get('status')!='success': raise RuntimeError(f'expiry failed: {r}')
        ds=[]
        for raw in r.get('data',[]):
            d=self._parse_expiry(raw)
            if d and d>=today: ds.append(d)
        if not ds: raise RuntimeError('No current/future NIFTY expiry found')
        v=min(ds).strftime('%d%b%y').upper(); self.expiry_cache_date=today; self.expiry_cache_value=v
        return v

    def _contract(self,direction):
        ot='CE' if direction=='BULLISH' else 'PE'
        r=self.client.optionsymbol(underlying=INDEX_SYMBOL,exchange=INDEX_EXCHANGE,expiry_date=self._nearest_expiry(),offset=OFFSET,option_type=ot)
        if r.get('status')!='success': raise RuntimeError(f'optionsymbol failed: {r}')
        symbol=str(r.get('symbol','')).upper(); ex=str(r.get('exchange',OPTIONS_EXCHANGE)).upper(); lot=int(float(r.get('lotsize') or 0))
        if not symbol or lot<=0: raise RuntimeError(f'bad contract: {r}')
        ltp=self._quote(symbol,ex)
        if ltp is None: raise RuntimeError('option LTP unavailable')
        if not self._option_ltp_sane(ltp): raise RuntimeError(f'option LTP sanity blocked {symbol}@{ltp:.2f}')
        return symbol,ex,ot,lot,ltp

    def _size(self,ltp,lot,move_class):
        risk_budget=TRADING_CAPITAL_RUPEES*RISK_PER_TRADE_PERCENT/100
        if move_class=='NORMAL':
            risk_budget*=NORMAL_RISK_MULTIPLIER
        capital_budget=TRADING_CAPITAL_RUPEES*MAX_CAPITAL_DEPLOYMENT_PERCENT/100
        cost=ltp*lot; risk=cost*HARD_STOP_PERCENT/100
        lr=int(risk_budget//risk) if risk>0 else 0; lc=int(capital_budget//cost) if cost>0 else 0
        lots=min(lr,lc)
        if lots<1: raise RuntimeError('sizing blocks entry')
        return lots,lots*lot

    def _maybe_arm(self):
        if self.signal or self.position or len(self.ticks)<WARMUP_SECONDS:return
        cur=self.ticks[-1].price
        old=self._price_ago(IMPULSE_WINDOW_SECONDS)
        state=self._acceleration_state()
        if old is None or state is None:return
        m1,m2,m3,up,down,gaps,bull_acc,bear_acc,bull_gap,bear_gap=state
        impulse=cur-old; noise=max(self._noise(),0.25); th=max(MIN_IMPULSE_POINTS,IMPULSE_NOISE_MULT*noise)
        p=self._recent_prices(8); ef=self._ema(p,FAST_EMA_PERIOD)
        if abs(cur-ef)>MAX_NIFTY_DISTANCE_FROM_FAST_EMA:return
        direction=None
        if impulse>=th and bull_acc and bull_gap:direction='BULLISH'
        elif impulse<=-th and bear_acc and bear_gap:direction='BEARISH'
        if not direction:return
        move_class,pullback_wait,max_age,chase_cap,min_confirm,ema_keep=self._move_profile(impulse)

        # V7: detect everything, but place orders only for explicitly enabled classes.
        class_enabled = ((move_class=='NORMAL' and ENABLE_NORMAL_ENTRIES) or
                         (move_class=='STRONG' and ENABLE_STRONG_ENTRIES) or
                         (move_class=='EXPLOSIVE' and ENABLE_EXPLOSIVE_ENTRIES))
        if not class_enabled:
            self.log(f'{move_class} {direction} MOVE DETECTED but entry class disabled by V7 quality gate')
            return

        # Strong setups must be genuinely strong, not merely just above the old 5-point boundary.
        if move_class=='STRONG':
            if abs(impulse) < STRONG_MIN_IMPULSE_POINTS:
                self.log(f'STRONG {direction} rejected: impulse {abs(impulse):.2f}<{STRONG_MIN_IMPULSE_POINTS:.2f}pt quality minimum')
                return
            if (direction=='BULLISH' and up < STRONG_REQUIRED_DIRECTIONAL_MOVES) or (direction=='BEARISH' and down < STRONG_REQUIRED_DIRECTIONAL_MOVES):
                self.log(f'STRONG {direction} rejected: directional consistency {up}/{down}, require {STRONG_REQUIRED_DIRECTIONAL_MOVES}/4 in trade direction')
                return
            if abs(gaps[2]) < STRONG_MIN_CURRENT_EMA_GAP_POINTS:
                self.log(f'STRONG {direction} rejected: EMA gap {gaps[2]:+.2f} too small (<{STRONG_MIN_CURRENT_EMA_GAP_POINTS:.2f})')
                return

        try:symbol,ex,ot,lot,opt=self._contract(direction)
        except Exception as e:self.log(f'FAST MOVE FOUND but contract lookup failed: {e}');return
        # Do not immediately re-enter the same direction after a failed trade unless cooldown has elapsed.
        if time.monotonic()-self.last_failed_direction_monotonic[direction] < FAILED_DIRECTION_COOLDOWN_SECONDS:
            return
        self.signal=Signal(direction,move_class,time.monotonic(),old,cur,impulse,symbol,ex,ot,lot,opt,cur,
                           pullback_wait,max_age,chase_cap,min_confirm,ema_keep,False,opt)
        mode_text='continuation' if move_class=='EXPLOSIVE' else 'micro-pullback/hold'
        self.log(
            f"{move_class} FAST {direction} MOVE ARMED: NIFTY={cur:.2f} | 1s={m1:+.2f} 2s={m2:+.2f} 3s={m3:+.2f} "
            f"| dir(up/down)={up}/{down} | EMAgap {gaps[0]:+.2f}->{gaps[1]:+.2f}->{gaps[2]:+.2f} "
            f"| noise={noise:.2f} threshold={th:.2f} | option_ref={symbol}@{opt:.2f} "
            f"| chase_cap=+{chase_cap:.2f}% min_confirm={min_confirm:+.2f}% | waiting for {mode_text}"
        )

    def _cancel_signal(self,reason):
        if self.signal:self.log(f'SIGNAL CANCELLED ({self.signal.direction}): {reason}')
        self.signal=None

    def _eval_signal(self):
        s=self.signal
        if not s or self.position:return
        age=time.monotonic()-s.armed_at; cur=self.ticks[-1].price
        if age>s.max_age_seconds:self._cancel_signal(f'{s.move_class} stale after {age:.2f}s');return
        retrace_fraction=(NORMAL_MAX_RETRACE_FRACTION if s.move_class=='NORMAL' else
                           (STRONG_MAX_PULLBACK_FRACTION if s.move_class=='STRONG' else MAX_PULLBACK_FRACTION))
        max_retrace=abs(s.impulse_points)*retrace_fraction
        if s.move_class=='NORMAL' and abs(s.impulse_points)<NORMAL_MIN_IMPULSE_FOR_ENTRY_POINTS:
            self._cancel_signal(f'NORMAL impulse too small for entry {abs(s.impulse_points):.2f}<{NORMAL_MIN_IMPULSE_FOR_ENTRY_POINTS:.2f}pt');return

        # Track a controlled pullback first. V6 never buys an explosive burst at its first extreme.
        if s.direction=='BULLISH':
            retrace=s.impulse_price-cur; s.pullback_extreme=min(s.pullback_extreme,cur)
            if retrace>max_retrace:self._cancel_signal(f'deep retrace {retrace:.2f}>{max_retrace:.2f}');return
            min_pb=(EXPLOSIVE_MIN_PULLBACK_POINTS if s.move_class=='EXPLOSIVE' else (abs(s.impulse_points)*STRONG_MIN_PULLBACK_FRACTION if s.move_class=='STRONG' else MIN_PULLBACK_POINTS))
            if retrace>=min_pb:s.saw_pullback=True
            second_impulse=cur-s.pullback_extreme if s.saw_pullback else 0.0
        else:
            retrace=cur-s.impulse_price; s.pullback_extreme=max(s.pullback_extreme,cur)
            if retrace>max_retrace:self._cancel_signal(f'deep retrace {retrace:.2f}>{max_retrace:.2f}');return
            min_pb=(EXPLOSIVE_MIN_PULLBACK_POINTS if s.move_class=='EXPLOSIVE' else (abs(s.impulse_points)*STRONG_MIN_PULLBACK_FRACTION if s.move_class=='STRONG' else MIN_PULLBACK_POINTS))
            if retrace>=min_pb:s.saw_pullback=True
            second_impulse=s.pullback_extreme-cur if s.saw_pullback else 0.0

        # For STRONG setups the second impulse must actually re-break the first impulse extreme.
        # This avoids buying an ordinary bounce that never resumes the original move.
        if s.move_class=='STRONG' and s.saw_pullback:
            if s.direction=='BULLISH' and cur < s.impulse_price + STRONG_REBREAK_BUFFER_POINTS:
                return
            if s.direction=='BEARISH' and cur > s.impulse_price - STRONG_REBREAK_BUFFER_POINTS:
                return

        # Track option premium throughout the setup so the final entry is a genuine local-premium breakout.
        opt=self._quote(s.symbol,s.exchange)
        if opt is None:return
        if not self._option_ltp_sane(opt):
            self._cancel_signal(f'option LTP sanity blocked {s.symbol}@{opt:.2f}');return
        prior_high=max(s.option_highest_ltp,s.option_ref_ltp)

        needed={'NORMAL':NORMAL_SECOND_IMPULSE_POINTS,'STRONG':STRONG_SECOND_IMPULSE_POINTS,'EXPLOSIVE':EXPLOSIVE_SECOND_IMPULSE_POINTS}[s.move_class]
        if not s.saw_pullback or second_impulse<needed:
            s.option_highest_ltp=max(s.option_highest_ltp,opt)
            return

        # Re-check NIFTY structure before allowing the option breakout to trigger entry.
        gaps=self._ema_gap_series()
        if gaps is None:self._cancel_signal('EMA gap unavailable');return
        g2,g1,g0=gaps
        if not self._ema_gap_holds(s.direction,gaps,s.ema_keep_ratio):
            self._cancel_signal(f'{s.move_class} EMA momentum weakened {g2:+.2f}->{g1:+.2f}->{g0:+.2f} (keep>={s.ema_keep_ratio:.0%})');return

        # Option must itself break above the highest premium observed since arming.
        breakout_required=prior_high*(1+OPTION_BREAKOUT_MIN_PERCENT/100)
        option_breakout=opt>=breakout_required
        jump=(opt/s.option_ref_ltp-1)*100
        if jump>s.option_chase_cap_percent:
            self._cancel_signal(f'{s.move_class} option already jumped {jump:+.2f}% > +{s.option_chase_cap_percent:.2f}%');return
        if jump<s.option_min_confirm_percent:
            s.option_highest_ltp=max(s.option_highest_ltp,opt)
            return
        if not option_breakout:
            s.option_highest_ltp=max(s.option_highest_ltp,opt)
            return

        self.log(
            f"{s.move_class} {s.direction} SECOND-IMPULSE + OPTION-BREAKOUT CONFIRMED after {age:.2f}s | "
            f"NIFTY={cur:.2f} second_impulse={second_impulse:.2f}pt | option {s.option_ref_ltp:.2f}->{opt:.2f} "
            f"({jump:+.2f}%) breakout>{prior_high:.2f} | EMAgap {g2:+.2f}->{g1:+.2f}->{g0:+.2f}"
        )
        self._enter(s,opt)

    def _wait_fill(self,oid):
        end=time.monotonic()+ORDER_FILL_TIMEOUT_SECONDS
        while time.monotonic()<end:
            try:
                r=self.client.orderstatus(order_id=oid,strategy=STRATEGY_NAME)
                if r.get('status')=='success':
                    d=r.get('data',{}); st=str(d.get('order_status','')).lower()
                    if st in {'complete','completed'}:
                        avg=float(d.get('average_price') or 0); q=int(float(d.get('quantity') or d.get('filled_quantity') or 0))
                        if avg>0 and q>0:return avg,q
                    if st in {'rejected','cancelled','canceled'}:return None
            except Exception:pass
            time.sleep(ORDER_STATUS_POLL_SECONDS)
        return None

    def _enter(self,s,opt):
        try:lots,qty=self._size(opt,s.lot_size,s.move_class)
        except Exception as e:self._cancel_signal(str(e));return
        self.log(f'SIZING [{s.move_class}]: {s.symbol} LTP={opt:.2f} | lot={s.lot_size} | lots={lots} | qty={qty} | deployment~Rs.{opt*qty:,.0f}')
        self.log(f'ENTRY BUY [{s.move_class}] {s.symbol} qty={qty} ({lots} lot(s)) MARKET')
        try:r=self.client.placeorder(strategy=STRATEGY_NAME,symbol=s.symbol,exchange=s.exchange,action='BUY',quantity=qty,price_type='MARKET',product=PRODUCT)
        except Exception as e:self._cancel_signal(f'BUY exception: {e}');return
        if r.get('status')!='success' or not r.get('orderid'):self._cancel_signal(f'BUY rejected: {r}');return
        fill=self._wait_fill(str(r['orderid']))
        if not fill:self._cancel_signal('BUY fill not verified');return
        avg,fq=fill
        self.position=Position(s.symbol,s.exchange,s.option_type,s.move_class,fq,avg,time.monotonic(),avg*(1-HARD_STOP_DISPATCH_PERCENT/100),entry_order_id=str(r['orderid']))
        self.daily_trade_count+=1; self.last_entry_monotonic=time.monotonic(); self.signal=None
        self.log(f'FILLED {s.symbol} avg={avg:.2f} qty={fq} | class={s.move_class} | stop_dispatch={self.position.hard_stop:.2f} (-{HARD_STOP_DISPATCH_PERCENT:.1f}%, risk model {HARD_STOP_PERCENT:.1f}%) | trail activates=+{PROFIT_TRAIL_ACTIVATION_PERCENT:.0f}%')

    def _exit(self,reason):
        p=self.position
        if not p:return
        held=time.monotonic()-p.entry_monotonic
        self.log(f'EXIT SELL {p.symbol} qty={p.quantity} MARKET | reason={reason}')
        try:r=self.client.placeorder(strategy=STRATEGY_NAME,symbol=p.symbol,exchange=p.exchange,action='SELL',quantity=p.quantity,price_type='MARKET',product=PRODUCT)
        except Exception as e:self.log(f'EXIT exception: {e}');return
        if r.get('status')!='success' or not r.get('orderid'):
            self.log(f'EXIT failed: {r}');return
        exit_oid=str(r['orderid'])
        fill=self._wait_fill(exit_oid)
        if not fill:
            self.log(f'EXIT WARNING: SELL order {exit_oid} submitted but fill was not verified; position retained for safety')
            return
        exit_avg,exit_qty=fill
        realized=(exit_avg/p.entry_price-1)*100
        self.completed_trades.append({
            'class':p.move_class,'option_type':p.option_type,'symbol':p.symbol,'qty':exit_qty,
            'entry':p.entry_price,'exit':exit_avg,'pnl_pct':realized,'peak_pct':p.peak_pnl_pct,
            'held_s':held,'reason':reason,'entry_order_id':p.entry_order_id,'exit_order_id':exit_oid,
        })
        self.log(f'EXIT FILLED {p.symbol} avg={exit_avg:.2f} qty={exit_qty} | realized={realized:+.2f}% | peak={p.peak_pnl_pct:+.2f}% | held={held:.1f}s | exit_order={exit_oid}')
        if realized<=0:
            failed_dir='BULLISH' if p.option_type=='CE' else 'BEARISH'
            self.last_failed_direction_monotonic[failed_dir]=time.monotonic()
            self.log(f'FAILED-DIRECTION COOLDOWN: {failed_dir} blocked for {FAILED_DIRECTION_COOLDOWN_SECONDS:.0f}s')
        self.position=None; self.last_entry_monotonic=time.monotonic()

    def _session_summary(self):
        n=len(self.completed_trades)
        if not n:
            self.log('SESSION SUMMARY: 0 completed trades.')
            return
        wins=[x for x in self.completed_trades if x['pnl_pct']>0]
        losses=[x for x in self.completed_trades if x['pnl_pct']<0]
        net=sum(x['pnl_pct'] for x in self.completed_trades)
        self.log('='*82)
        self.log(f'SESSION SUMMARY: trades={n} | wins={len(wins)} | losses={len(losses)} | sum(realized % per trade)={net:+.2f}%')
        for cls in ('NORMAL','STRONG','EXPLOSIVE'):
            rows=[x for x in self.completed_trades if x['class']==cls]
            if rows:
                cw=sum(1 for x in rows if x['pnl_pct']>0); cn=sum(x['pnl_pct'] for x in rows)
                self.log(f'CLASS SUMMARY {cls}: trades={len(rows)} wins={cw} losses={len(rows)-cw} winrate={100*cw/len(rows):.1f}% sum_realized={cn:+.2f}%')
        for i,x in enumerate(self.completed_trades,1):
            self.log(f"TRADE {i:02d}: {x['class']} {x['option_type']} {x['symbol']} qty={x['qty']} | entry={x['entry']:.2f} exit={x['exit']:.2f} | realized={x['pnl_pct']:+.2f}% peak={x['peak_pct']:+.2f}% | held={x['held_s']:.1f}s | reason={x['reason']} | entry_order={x['entry_order_id']} exit_order={x['exit_order_id']}")
        self.log('='*82)

    def _fast_reversal(self,ot):
        if len(self.ticks)<5:return False
        cur=self.ticks[-1].price; old=self._price_ago(REVERSAL_WINDOW_SECONDS)
        if old is None:return False
        move=cur-old; noise=max(self._noise(),0.25); th=max(REVERSAL_MIN_POINTS,REVERSAL_NOISE_MULTIPLIER*noise)
        p=self._recent_prices(6); ef=self._ema(p,FAST_EMA_PERIOD); es=self._ema(p,SLOW_EMA_PERIOD)
        return (ot=='CE' and move<=-th and ef<es) or (ot=='PE' and move>=th and ef>es)


    def _momentum_weakening(self,ot):
        gaps=self._ema_gap_series()
        if gaps is None:return False
        _,g1,g0=gaps
        if ot=='CE':
            return g0<=0 or (g1>0 and g0<g1*0.80)
        return g0>=0 or (g1<0 and abs(g0)<abs(g1)*0.80)

    def _momentum_faded(self,ot):
        gaps=self._ema_gap_series()
        if gaps is None:return False
        _,_,g0=gaps
        return (ot=='CE' and g0<=0) or (ot=='PE' and g0>=0)

    def _manage(self):
        p=self.position
        if not p:return
        ltp=self._quote(p.symbol,p.exchange)
        if ltp is None:return
        pnl=(ltp/p.entry_price-1)*100; p.peak_pnl_pct=max(p.peak_pnl_pct,pnl)
        if ltp<=p.hard_stop:self._exit(f'HARD STOP DISPATCH {pnl:+.2f}% (trigger -{HARD_STOP_DISPATCH_PERCENT:.1f}%)');return
        held=time.monotonic()-p.entry_monotonic

        # If the trade never follows through almost immediately, leave before a full momentum-fade loss.
        if (held>=NO_FOLLOW_THROUGH_SECONDS and p.peak_pnl_pct<NO_FOLLOW_THROUGH_MIN_PEAK_PERCENT and
            self._momentum_weakening(p.option_type)):
            self._exit(f'NO FOLLOW-THROUGH after {held:.1f}s | pnl={pnl:+.2f}% peak={p.peak_pnl_pct:+.2f}%');return

        # Staged early profit protection from the distribution seen in the V5 full-day test.
        early_floor=None
        if p.peak_pnl_pct>=SOFT_PROFIT_STEP2_ARM_PERCENT: early_floor=SOFT_PROFIT_STEP2_FLOOR_PERCENT
        elif p.peak_pnl_pct>=SOFT_PROFIT_ARM_PERCENT: early_floor=SOFT_PROFIT_FLOOR_PERCENT
        if early_floor is not None and not p.trailing_active and held>=SOFT_PROFIT_MIN_HOLD_SECONDS and pnl<=early_floor:
            self._exit(f'EARLY PROFIT PROTECT pnl={pnl:+.2f}% peak={p.peak_pnl_pct:+.2f}% floor=+{early_floor:.2f}%');return

        # Direct giveback guard below the full +2% trail.
        if (0.75<=p.peak_pnl_pct<PROFIT_TRAIL_ACTIVATION_PERCENT and
            p.peak_pnl_pct-pnl>=EARLY_PEAK_GIVEBACK_PERCENT):
            self._exit(f'EARLY PEAK GIVEBACK pnl={pnl:+.2f}% peak={p.peak_pnl_pct:+.2f}% giveback={p.peak_pnl_pct-pnl:.2f}%');return

        if p.peak_pnl_pct>=PROFIT_TRAIL_ACTIVATION_PERCENT:p.trailing_active=True
        if p.trailing_active:
            floor=max(PROFIT_TRAIL_MIN_FLOOR_PERCENT,p.peak_pnl_pct-PROFIT_TRAIL_GIVEBACK_PERCENT); p.trailing_floor_pct=max(p.trailing_floor_pct,floor)
            if pnl<=p.trailing_floor_pct:self._exit(f'PROFIT TRAIL pnl={pnl:+.2f}% floor={p.trailing_floor_pct:+.2f}% peak={p.peak_pnl_pct:+.2f}%');return
        if self._fast_reversal(p.option_type):self._exit('NIFTY fast reversal against held option');return
        if held>=MIN_HOLD_BEFORE_MOMENTUM_EXIT_SECONDS and self._momentum_faded(p.option_type):
            self._exit(f'EMA MOMENTUM FADE after {held:.0f}s | pnl={pnl:+.2f}% peak={p.peak_pnl_pct:+.2f}%');return
        if held>=MAX_HOLD_SECONDS:self._exit(f'MAX HOLD {MAX_HOLD_SECONDS}s');return
        now_m=time.monotonic()
        if now_m-p.last_status_log_monotonic>=1.0:
            p.last_status_log_monotonic=now_m
            self.log(f'POSITION {p.symbol}: LTP={ltp:.2f} | entry={p.entry_price:.2f} | PnL={pnl:+.2f}% | peak={p.peak_pnl_pct:+.2f}% | trail_floor={p.trailing_floor_pct:+.2f}%')

    def run(self):
        self.log('='*82); self.log('NIFTY50 1-SECOND FAST MOVE SCALPER VALIDATED QUALITY V7')
        self.log(f'Capital=Rs.{TRADING_CAPITAL_RUPEES:,.0f} | risk/trade={RISK_PER_TRADE_PERCENT:.2f}% | hard stop={HARD_STOP_PERCENT:.1f}%')
        self.log(f'Classes: NORMAL <{STRONG_MOVE_POINTS:.1f}pt | STRONG {STRONG_MOVE_POINTS:.1f}-{EXPLOSIVE_MOVE_POINTS:.1f}pt | EXPLOSIVE >={EXPLOSIVE_MOVE_POINTS:.1f}pt (3s move)')
        self.log(f'Adaptive chase caps: NORMAL +{NORMAL_OPTION_CHASE_CAP_PERCENT:.2f}% | STRONG +{STRONG_OPTION_CHASE_CAP_PERCENT:.1f}% | EXPLOSIVE +{EXPLOSIVE_OPTION_CHASE_CAP_PERCENT:.1f}% (>=10pt +{EXPLOSIVE_10PT_CHASE_CAP_PERCENT:.1f}%)')
        self.log(f'Option contradiction floors: NORMAL {NORMAL_OPTION_MIN_CONFIRM_PERCENT:+.2f}% | STRONG {STRONG_OPTION_MIN_CONFIRM_PERCENT:+.2f}% | EXPLOSIVE {EXPLOSIVE_OPTION_MIN_CONFIRM_PERCENT:+.2f}%')
        self.log(f'NORMAL tightening: min impulse {NORMAL_MIN_IMPULSE_FOR_ENTRY_POINTS:.1f}pt | confirm >={NORMAL_OPTION_MIN_CONFIRM_PERCENT:+.2f}% | retrace<={NORMAL_MAX_RETRACE_FRACTION:.0%} | risk x{NORMAL_RISK_MULTIPLIER:.2f}')
        self.log(f'Stop dispatch at -{HARD_STOP_DISPATCH_PERCENT:.1f}% with {POSITION_MONITOR_INTERVAL_SECONDS:.2f}s position monitoring | risk sizing still models {HARD_STOP_PERCENT:.1f}%')
        self.log(f'V6 exits: no-follow-through {NO_FOLLOW_THROUGH_SECONDS:.0f}s | early floors +{SOFT_PROFIT_ARM_PERCENT:.2f}%=>+{SOFT_PROFIT_FLOOR_PERCENT:.2f}%, +{SOFT_PROFIT_STEP2_ARM_PERCENT:.2f}%=>+{SOFT_PROFIT_STEP2_FLOOR_PERCENT:.2f}% | full trail +{PROFIT_TRAIL_ACTIVATION_PERCENT:.2f}%')
        self.log(f'Session safety: last new entry {ENTRY_CUTOFF.strftime("%H:%M:%S")} | proactive force-flat {FORCE_CLOSE.strftime("%H:%M:%S")} | emergency final sweep {FINAL_SWEEP.strftime("%H:%M:%S")}')
        self.log(f'V7 quality gate: NORMAL={ENABLE_NORMAL_ENTRIES} STRONG={ENABLE_STRONG_ENTRIES} EXPLOSIVE={ENABLE_EXPLOSIVE_ENTRIES} | entry start {ENTRY_START.strftime("%H:%M:%S")}')
        self.log(f'STRONG validation: >= {STRONG_MIN_IMPULSE_POINTS:.1f}pt | 4/4 direction | EMA gap >= {STRONG_MIN_CURRENT_EMA_GAP_POINTS:.2f} | pullback {STRONG_MIN_PULLBACK_FRACTION:.0%}-{STRONG_MAX_PULLBACK_FRACTION:.0%} | re-break + option breakout')
        self.log(f'Data guard: quarantine >{MAX_VALID_1S_SPOT_JUMP_POINTS:.0f}pt one-second NIFTY discontinuity; option sanity Rs.{MIN_REASONABLE_OPTION_LTP:.0f}-Rs.{MAX_REASONABLE_OPTION_LTP:.0f}')
        self.log('='*82)
        next_spot_tick=time.monotonic()
        next_position_check=time.monotonic()
        while True:
            self._roll_day(); now=self.now(); t=now.time()
            if t>=MARKET_CLOSE:
                if self.position:self._exit('market close')
                self._session_summary(); self.log('Market session complete.');break
            if t<MARKET_OPEN:time.sleep(1);continue
            if t>=ENTRY_CUTOFF and self.signal:
                self._cancel_signal(f'entry cutoff reached at {ENTRY_CUTOFF.strftime("%H:%M:%S")}')
            if t>=FORCE_CLOSE and self.position:self._exit(f'proactive force close before broker MIS cutoff ({FORCE_CLOSE.strftime("%H:%M:%S")})')
            if t>=FINAL_SWEEP and not self.final_sweep_done:
                self.final_sweep_done=True
                if self.signal:self._cancel_signal(f'15:25 final sweep - no pending entries allowed')
                if self.position:
                    self._exit(f'15:25 FINAL EMERGENCY SQUARE-OFF SWEEP')
                else:
                    self.log('15:25 FINAL SWEEP: no tracked open position; strategy flat')
            mono=time.monotonic()

            # Preserve 1-second NIFTY sampling for signal/EMA calculations.
            if mono>=next_spot_tick:
                next_spot_tick=mono+SAMPLE_INTERVAL_SECONDS
                spot=self._quote(INDEX_SYMBOL,INDEX_EXCHANGE)
                if spot is None:
                    self.log('DATA WARNING: NIFTY quote unavailable')
                else:
                    if self._spot_tick_is_usable(spot):
                        self.ticks.append(Tick(time.monotonic(),spot))
                        if not self.position:
                            if self.signal:self._eval_signal()
                            elif ENTRY_START<=t<ENTRY_CUTOFF and time.monotonic()-self.last_entry_monotonic>=GLOBAL_POST_TRADE_COOLDOWN_SECONDS:
                                if len(self.ticks)<WARMUP_SECONDS:
                                    if len(self.ticks)%10==0:self.log(f'WARMUP: {len(self.ticks)}/{WARMUP_SECONDS} samples | NIFTY={spot:.2f}')
                                else:
                                    self._maybe_arm()

            # Once a position exists, monitor option risk faster than the 1-second signal clock.
            if self.position and mono>=next_position_check:
                next_position_check=mono+POSITION_MONITOR_INTERVAL_SECONDS
                self._manage()

            time.sleep(0.02)

if __name__=='__main__':
    try: Scalper().run()
    except KeyboardInterrupt: print('Stopped by user.',flush=True)
    except Exception as exc: print(f'FATAL: {exc}',flush=True); raise
