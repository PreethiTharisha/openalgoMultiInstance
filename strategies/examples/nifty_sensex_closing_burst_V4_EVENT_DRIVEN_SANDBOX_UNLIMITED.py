"""
OpenAlgo NIFTY/SENSEX Closing Burst V4 - Event Driven (SANDBOX-FIRST)

No EMA crossover. Uses actual incoming tick timestamps, burst scoring,
pre-streamed ATM/ITM1/ITM2 CE/PE, option-premium confirmation, diagnostics,
normal-close vs expiry-day profiles, micro-reversal exits and forced EOD flat.

Required env: OPENALGO_API_KEY
Optional: HOST_SERVER, WS_URL, QUICK_INDEX=NIFTY|SENSEX, QUICK_LOTS=1, QUICK_PRODUCT=NRML
"""
from __future__ import annotations
import os, time, math, threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, time as dtime
import numpy as np
import pytz
from openalgo import api

INDEX=os.getenv('QUICK_INDEX','NIFTY').upper(); LOTS=int(os.getenv('QUICK_LOTS','1')); PRODUCT=os.getenv('QUICK_PRODUCT','NRML')
STRATEGY=f'{INDEX}_CLOSING_BURST_V4'; HOST=os.getenv('HOST_SERVER','http://127.0.0.1:5004'); WS_URL=os.getenv('WS_URL','ws://127.0.0.1:8768')
API_KEY=os.getenv('OPENALGO_API_KEY','').strip()
if not API_KEY: raise RuntimeError('OPENALGO_API_KEY environment variable is not set')
if INDEX=='NIFTY': UEX='NSE_INDEX'; OEX='NFO'; BASE_TRIGGER=3.20; MIN_FAST_MOVE=1.8
elif INDEX=='SENSEX': UEX='BSE_INDEX'; OEX='BFO'; BASE_TRIGGER=3.40; MIN_FAST_MOVE=6.0
else: raise ValueError('QUICK_INDEX must be NIFTY or SENSEX')

IST=pytz.timezone('Asia/Kolkata'); client=api(api_key=API_KEY,host=HOST,ws_url=WS_URL)
WARM=dtime(15,14,35); START=dtime(15,15); HI=dtime(15,20); ULTRA=dtime(15,27); LAST_ENTRY=dtime(15,29); FORCE_EXIT=dtime(15,29,40)
OFFSETS=('ATM','ITM1','ITM2'); RAW_SAMPLES=3; HEARTBEAT_SEC=2.0
MAX_CONSEC_LOSSES=3; SIGNAL_REFRACTORY=0.60; EVAL_SEC=0.02; MIN_HOLD=0.45

u_ticks=deque(maxlen=12000); o_ticks={}; lock=threading.Lock(); contracts=[]; contracts_lock=threading.Lock(); subscribed_opts=[]
raw_u=raw_o=total_u=total_o=0; last_u_ts=0.0
position=None; last_signal=last_exit=0.0; trades=consec_losses=0

def now(): return datetime.now(IST)
def log(s): print(f'[{now():%Y-%m-%d %H:%M:%S.%f} IST] {s}',flush=True)
def parse_exp(s): return datetime.strptime(s.upper(),'%d-%b-%y')

def nearest_expiry():
    r=client.expiry(symbol=INDEX,exchange=OEX,instrumenttype='options')
    if not isinstance(r,dict) or r.get('status')!='success': raise RuntimeError(f'Expiry lookup failed: {r}')
    today=now().date(); vals=[]
    for x in r.get('data',[]):
        try:
            d=parse_exp(str(x))
            if d.date()>=today: vals.append((d,str(x)))
        except: pass
    if not vals: raise RuntimeError(f'No current/future expiry: {r}')
    vals.sort(key=lambda z:z[0]); d,raw=vals[0]
    return d.strftime('%d%b%y').upper(), d.date()==today

def resolve(side,expiry,offset):
    r=client.optionsymbol(underlying=INDEX,exchange=UEX,expiry_date=expiry,offset=offset,option_type=side)
    if not isinstance(r,dict) or r.get('status')!='success': raise RuntimeError(f'optionsymbol {side} {offset} failed: {r}')
    return {'side':side,'offset':offset,'symbol':str(r['symbol']),'exchange':str(r.get('exchange',OEX)),'lotsize':int(r['lotsize'])}

def flatten(p):
    out=[]
    if isinstance(p,dict):
        out.append(p); d=p.get('data')
        if isinstance(d,dict): out.append(d)
        elif isinstance(d,list): out.extend(x for x in d if isinstance(x,dict))
    return out

def ext_ltp(p):
    for d in flatten(p):
        for k in ('ltp','last_price','price','close','last'):
            try:
                if k in d: return float(d[k])
            except: pass
    return None

def ext_sym(p):
    for d in flatten(p):
        for k in ('symbol','tradingsymbol','instrument','ticker'):
            if d.get(k): return str(d[k])
    return None

def on_u(payload):
    global raw_u,total_u,last_u_ts
    if raw_u<RAW_SAMPLES: raw_u+=1; log(f'RAW UNDERLYING WS #{raw_u}: {payload}')
    px=ext_ltp(payload)
    if px is None or px<=0: return
    ts=time.time()
    with lock: u_ticks.append((ts,px))
    total_u+=1; last_u_ts=ts

def on_o(payload):
    global raw_o,total_o
    if raw_o<RAW_SAMPLES: raw_o+=1; log(f'RAW OPTION WS #{raw_o}: {payload}')
    px=ext_ltp(payload); sym=ext_sym(payload)
    if px is None or px<=0 or not sym: return
    with lock:
        o_ticks.setdefault(sym,deque(maxlen=8000)).append((time.time(),px))
    total_o+=1

def snap_u():
    with lock: return list(u_ticks)
def snap_o(sym):
    with lock: return list(o_ticks.get(sym,()))
def latest(arr): return arr[-1][1] if arr else None

def event_move(arr,min_age,max_age):
    if len(arr)<2: return None
    n=time.time(); t1,p1=arr[-1]; cand=None
    for t0,p0 in reversed(arr[:-1]):
        age=n-t0
        if age<min_age: continue
        if age>max_age: break
        cand=(t0,p0); break
    if cand is None: return None
    t0,p0=cand; dt=max(t1-t0,1e-6); mv=p1-p0
    return {'dt':dt,'move':mv,'velocity':mv/dt,'from':p0,'to':p1}

def noise_v(arr,lookback=8.0):
    cutoff=time.time()-lookback; xs=[x for x in arr if x[0]>=cutoff]
    if len(xs)<6: return 0.0
    vals=[]
    for i in range(1,len(xs)):
        dt=xs[i][0]-xs[i-1][0]
        if dt>0: vals.append(abs((xs[i][1]-xs[i-1][1])/dt))
    return float(np.percentile(vals,70)) if vals else 0.0

def consistency(arr,lookback=.9):
    xs=[x for x in arr if x[0]>=time.time()-lookback]
    if len(xs)<4: return 0.0
    d=np.diff([p for _,p in xs]); d=d[np.abs(d)>1e-9]
    return float(np.sum(np.sign(d))/len(d)) if len(d) else 0.0

def sens_factor(t,expiry_day):
    x=1.0
    if t>=HI: x*=.90
    if t>=ULTRA: x*=.82
    if expiry_day: x*=.90
    return max(x,.65)

def metrics(expiry_day):
    arr=snap_u()
    if len(arr)<5: return None
    f=event_move(arr,.18,.70); m=event_move(arr,.55,1.60); s=event_move(arr,1.40,3.50)
    if not f or not m: return None
    nv=noise_v(arr); cons=consistency(arr); vf,vm=f['velocity'],m['velocity']; vs=s['velocity'] if s else vm; acc=vf-vm
    denom=max(nv,.50 if INDEX=='NIFTY' else 2.0)
    nvf,nvm,nvs,nacc=vf/denom,vm/denom,vs/denom,acc/denom
    bull=max(nvf,0)*1.2+max(nvm,0)*.75+max(nvs,0)*.35+max(nacc,0)*.5+max(cons,0)*.8
    bear=max(-nvf,0)*1.2+max(-nvm,0)*.75+max(-nvs,0)*.35+max(-nacc,0)*.5+max(-cons,0)*.8
    return {'spot':arr[-1][1],'fast':f,'mid':m,'slow':s,'noise':nv,'cons':cons,'acc':acc,'bull':bull,'bear':bear,'trigger':BASE_TRIGGER*sens_factor(now().time(),expiry_day)}

def preload(expiry):
    global subscribed_opts
    found=[]
    for side in ('CE','PE'):
        for off in OFFSETS:
            try: found.append(resolve(side,expiry,off))
            except Exception as e: log(f'Contract preload skipped {side} {off}: {e}')
    uniq=[]; seen=set()
    for c in found:
        k=(c['exchange'],c['symbol'])
        if k not in seen: uniq.append(c); seen.add(k)
    if not uniq: raise RuntimeError('No option contracts resolved')
    with contracts_lock: contracts[:] = uniq
    with lock:
        for c in uniq: o_ticks.setdefault(c['symbol'],deque(maxlen=8000))
    subscribed_opts=[{'exchange':c['exchange'],'symbol':c['symbol']} for c in uniq]
    try: client.subscribe_ltp(subscribed_opts,on_data_received=on_o)
    except Exception as e: log(f'Option websocket subscribe warning: {e}')
    log('Pre-streamed options: '+', '.join(f"{c['offset']} {c['symbol']}" for c in uniq))

def quote_data(c):
    r=client.quotes(symbol=c['symbol'],exchange=c['exchange'])
    if not isinstance(r,dict) or r.get('status')!='success': raise RuntimeError(f"quotes failed {c['symbol']}: {r}")
    return r.get('data',{})

def option_quality(c,expiry_day):
    d=quote_data(c); ltp=float(d.get('ltp',0) or 0); bid=ask=None
    for k in ('bid','best_bid','bid_price'):
        try:
            if d.get(k) is not None: bid=float(d[k]); break
        except: pass
    for k in ('ask','best_ask','ask_price'):
        try:
            if d.get(k) is not None: ask=float(d[k]); break
        except: pass
    spread=None
    if bid and ask and ask>=bid:
        mid=(bid+ask)/2
        if mid>0: spread=(ask-bid)/mid*100
    minprem=8.0 if expiry_day else 20.0; maxspr=6.0 if expiry_day else 4.0
    ok=ltp>=minprem and (spread is None or spread<=maxspr)
    return {'ltp':ltp,'spread':spread,'ok':ok}

def choose(side,expiry_day):
    with contracts_lock: cands=[dict(c) for c in contracts if c['side']==side]
    ranked=[]
    for c in cands:
        arr=snap_o(c['symbol']); f=event_move(arr,.15,.65); m=event_move(arr,.50,1.50)
        try: q=option_quality(c,expiry_day)
        except Exception as e: log(f"Quote check warning {c['symbol']}: {e}"); q={'ltp':latest(arr) or 0,'spread':None,'ok':bool(arr)}
        if not q['ok']: continue
        if f and m:
            if f['velocity']<=0: continue
            acc=f['velocity']-m['velocity']; ps=max(f['velocity'],0)+.5*max(acc,0)
        else: ps=.10
        bonus=.20 if c['offset']=='ITM1' else (.08 if c['offset']=='ATM' else 0)
        penalty=(q['spread'] or 0)*.03
        ranked.append((ps+bonus-penalty,c,q,f,m))
    if not ranked: return None
    ranked.sort(key=lambda x:x[0],reverse=True); return ranked[0]

def wait_fill(order_id,timeout=6.0):
    end=time.time()+timeout; last=None
    while time.time()<end:
        r=client.orderstatus(order_id=order_id,strategy=STRATEGY); last=r
        try:
            d=r['data']
            if str(d.get('order_status','')).lower()=='complete':
                px=float(d.get('average_price',0) or 0)
                if px>0: return px
        except: pass
        time.sleep(.08)
    raise RuntimeError(f'Order not complete within {timeout}s: {last}')

def order(sym,exch,action,qty):
    r=client.placeorder(strategy=STRATEGY,symbol=sym,action=action,exchange=exch,price_type='MARKET',product=PRODUCT,quantity=qty)
    if not isinstance(r,dict) or r.get('status')!='success': raise RuntimeError(f'Order rejected: {r}')
    oid=str(r.get('orderid')); return oid,wait_fill(oid)

@dataclass
class Pos:
    side:str; symbol:str; exchange:str; qty:int; entry:float; entry_time:float; peak:float=0.0; floor:float|None=None

def profile(expiry_day):
    return {'sl':8.0 if expiry_day else 9.0,'arm':6.0 if expiry_day else 8.0,'step':3.0 if expiry_day else 4.0,'cool':5.0 if expiry_day else 7.0,'maxtr':8 if expiry_day else 6}

def floor_from_peak(pk,expiry_day):
    if expiry_day:
        if pk<6:return None
        if pk<10:return 0.0
        if pk<16:return 4.0
        return 9.0+math.floor((pk-16)/3.0)*3.0
    else:
        if pk<8:return None
        if pk<12:return 0.0
        if pk<20:return 5.0
        return 12.0+math.floor((pk-20)/4.0)*4.0

def latest_opt(p):
    x=latest(snap_o(p.symbol))
    if x and x>0:return x
    d=client.quotes(symbol=p.symbol,exchange=p.exchange)
    if isinstance(d,dict) and d.get('status')=='success': return float(d['data']['ltp'])
    raise RuntimeError(f'No LTP for {p.symbol}: {d}')

def enter(side,m,expiry_day):
    global position,trades
    pick=choose(side,expiry_day)
    if not pick: log(f'BURST {side} rejected: no eligible option candidate'); return False
    score,c,q,f,om=pick; qty=c['lotsize']*LOTS
    log(f"BURST {side} spot={m['spot']:.2f} B={m['bull']:.2f} S={m['bear']:.2f} trig={m['trigger']:.2f} fast={m['fast']['move']:+.2f}/{m['fast']['dt']*1000:.0f}ms v={m['fast']['velocity']:+.2f} acc={m['acc']:+.2f} cons={m['cons']:+.2f} -> {c['offset']} {c['symbol']} spread={q['spread']}")
    oid,fill=order(c['symbol'],c['exchange'],'BUY',qty); position=Pos(side,c['symbol'],c['exchange'],qty,fill,time.time()); trades+=1
    log(f"ENTRY FILLED {c['symbol']} qty={qty} avg={fill:.2f} order={oid}"); return True

def exit_pos(reason):
    global position,last_exit,consec_losses
    p=position
    if not p:return
    try: oid,fill=order(p.symbol,p.exchange,'SELL',p.qty)
    except Exception as e: log(f'CRITICAL EXIT FAILED {p.symbol}: {e}'); return
    pnl=(fill/p.entry-1)*100; rs=(fill-p.entry)*p.qty
    log(f"EXIT {reason}: {p.symbol} entry={p.entry:.2f} exit={fill:.2f} PnL={pnl:+.2f}% / Rs {rs:+.2f} order={oid}")
    consec_losses=consec_losses+1 if pnl<0 else 0; position=None; last_exit=time.time()

def manage(expiry_day):
    p=position
    if not p:return
    pr=profile(expiry_day); ltp=latest_opt(p); pnl=(ltp/p.entry-1)*100; p.peak=max(p.peak,pnl); p.floor=floor_from_peak(p.peak,expiry_day)
    if pnl<=-pr['sl']: exit_pos('HARD_SL'); return
    if p.floor is not None and pnl<=p.floor: exit_pos(f'BURST_TRAIL floor={p.floor:.1f}% peak={p.peak:.1f}%'); return
    if time.time()-p.entry_time>=MIN_HOLD:
        ua=snap_u(); f=event_move(ua,.15,.65); m=event_move(ua,.45,1.40); of=event_move(snap_o(p.symbol),.12,.60)
        if f and m:
            urev=(f['velocity']<0 and m['velocity']<0) if p.side=='CE' else (f['velocity']>0 and m['velocity']>0)
            orev=bool(of and of['velocity']<0)
            if pnl>=1.5 and urev and orev: exit_pos('MICRO_REVERSAL_PROFIT'); return
            if p.peak>=5.0 and pnl<=.5 and urev: exit_pos('BURST_FAILED_AFTER_PROFIT'); return
    log(f"HOLD {p.symbol} LTP={ltp:.2f} PnL={pnl:+.2f}% peak={p.peak:+.2f}% floor={p.floor}")

def heartbeat(start):
    arr=snap_u(); lp=latest(arr); age=time.time()-last_u_ts if last_u_ts else None; tps=total_u/max(time.time()-start,1e-6)
    with contracts_lock:nc=len(contracts)
    log(f"WS HEARTBEAT underlyingTicks={total_u} avgTicksPerSec={tps:.2f} lastLTP={lp if lp is not None else 'NA'} lastTickAge={age if age is not None else 'NA'} optionTicks={total_o} optionStreams={nc}")

def main():
    global last_signal
    log('='*108); log(f'START {STRATEGY} | {INDEX} | lots={LOTS} | product={PRODUCT}')
    log('NO EMA CROSSOVER | EVENT-DRIVEN ticks + burst score + option acceleration'); log('SANDBOX-FIRST: validate before live deployment')
    expiry,expiry_day=nearest_expiry(); pr=profile(expiry_day)
    log(f"Nearest expiry={expiry} | expiry_day={expiry_day} | hardSL={pr['sl']}% | arm={pr['arm']}% | trailStep={pr['step']}% | cooldown={pr['cool']}s")
    ui=[{'exchange':UEX,'symbol':INDEX}]; client.connect(); client.subscribe_ltp(ui,on_data_received=on_u); log(f'Underlying websocket subscribed: {UEX}:{INDEX}')
    start=time.time(); last_hb=last_scan=0.0; options_loaded=False
    try:
        while True:
            global position
            t=now().time(); ep=time.time()
            if ep-last_hb>=HEARTBEAT_SEC: heartbeat(start); last_hb=ep
            if t>=WARM and not options_loaded:
                try: preload(expiry); options_loaded=True
                except Exception as e: log(f'Option preload failed: {e}'); time.sleep(.5); continue
            if t>=FORCE_EXIT:
                if position: exit_pos('FORCE_EOD')
                log('Closing-burst session finished.'); break
            if position:
                try: manage(expiry_day)
                except Exception as e: log(f'Position monitor warning: {e}')
                time.sleep(.06); continue
            if not (START<=t<=LAST_ENTRY) or not options_loaded: time.sleep(.05); continue
            if trades>=pr['maxtr']: time.sleep(.2); continue
            if consec_losses>=MAX_CONSEC_LOSSES:
                if ep-last_scan>=3: log('Trading paused: max consecutive losses reached.'); last_scan=ep
                time.sleep(.2); continue
            if ep-last_exit<pr['cool']: time.sleep(.02); continue
            m=metrics(expiry_day)
            if m is None:
                if ep-last_scan>=1: log('SCAN waiting for sufficient valid underlying ticks'); last_scan=ep
                time.sleep(EVAL_SEC); continue
            side=None; fm=abs(m['fast']['move'])
            if m['bull']>=m['trigger'] and m['bull']>m['bear']*1.2 and fm>=MIN_FAST_MOVE and m['fast']['velocity']>0: side='CE'
            elif m['bear']>=m['trigger'] and m['bear']>m['bull']*1.2 and fm>=MIN_FAST_MOVE and m['fast']['velocity']<0: side='PE'
            if side and ep-last_signal>=SIGNAL_REFRACTORY:
                last_signal=ep
                try: enter(side,m,expiry_day)
                except Exception as e: log(f'ENTRY FAILED: {e}'); time.sleep(.15)
            elif ep-last_scan>=.75:
                f=m['fast']; log(f"SCAN spot={m['spot']:.2f} fast={f['move']:+.2f}/{f['dt']*1000:.0f}ms vF={f['velocity']:+.2f} acc={m['acc']:+.2f} cons={m['cons']:+.2f} scoreB={m['bull']:.2f} scoreS={m['bear']:.2f} trigger={m['trigger']:.2f} noiseV={m['noise']:.2f}"); last_scan=ep
            time.sleep(EVAL_SEC)
    except KeyboardInterrupt:
        log('KeyboardInterrupt received.')
        if position:
            try: exit_pos('MANUAL_STOP')
            except Exception as e: log(f'Manual-stop exit failed: {e}')
    finally:
        try:
            if subscribed_opts: client.unsubscribe_ltp(subscribed_opts)
        except: pass
        try: client.unsubscribe_ltp(ui)
        except: pass
        try: client.disconnect()
        except: pass
        log('Strategy stopped.')

if __name__=='__main__': main()
