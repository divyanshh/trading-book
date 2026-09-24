"""Frozen historical-entry experiment, 24 September 2026.
Needs an equity-service checkout at 1758ac66dbe3ff10c71b4984a1a1dbb341c414b1,
its Python dependencies, and the original trusted local OHLC panel pickle.
Example: python replay.py --service /path/to/equity-service --panel /path/to/panel.pkl --output /tmp/fixed-replay
No database/broker/network calls. See README.md for limitations and hashes.
"""
from pathlib import Path
from decimal import Decimal
import argparse,sys,os,json
import pandas as pd,numpy as np
sys.dont_write_bytecode=True
parser=argparse.ArgumentParser()
parser.add_argument('--service',type=Path,required=True)
parser.add_argument('--panel',type=Path,required=True)
parser.add_argument('--inputs',type=Path,default=Path(__file__).with_name('inputs.csv'))
parser.add_argument('--output',type=Path,required=True)
a=parser.parse_args();P=a.output;P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(a.service));sys.path.append(str(a.service/'.venv/lib/python3.12/site-packages'))
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
import django
django.setup()
from trade_service.trading.services import trailing
S=pd.read_csv(a.inputs,float_precision='round_trip');S['id']=S.id.astype(int)
S['ed']=pd.to_datetime(S.ed);S['xd']=pd.to_datetime(S.xd);S=S.sort_values(['ed','id'])
E=S.set_index('id');raw=pd.read_pickle(a.panel)
END=pd.Timestamp('2026-09-22');ns={'END':END}
def dec(x):return Decimal(str(float(x)))
ACTIONS={'MCX':[('2026-01-02',5.)],'SHILPAMED':[('2025-10-03',2.)],
         'POCL':[('2026-07-21',2.5)],'TDPOWERSYS':[('2026-08-24',2.)]}
frames={}
for s in set(S.s):
 df=raw[s].copy();df['factor']=1.
 for dt,f in ACTIONS.get(s,[]):df.loc[df.index>=dt,'factor']*=f
 # Smooth normalized share units. Each simulation converts back to that
 # session's raw price before calling production rounding/stop functions.
 for c in ['o','h','l','c']:df[c+'_economic']=df[c]*df.factor
 df['ma20_economic_prior']=df.c_economic.rolling(20).mean().shift(1)
 frames[s]=df

def outcome(row,stop,mode='close',timing='close',defensive=False,entry_low=False,horizon=None,entry_override=None):
 df=frames[row.s];bars=df.loc[row.ed:END]
 if horizon:bars=bars.iloc[:horizon]
 ep=float(entry_override or row.entry)
 if not len(bars) or not 0<stop<ep:return None
 initial=stop;pending=False;why='open@end';day=bars.index[-1];xraw=float(bars.c.iloc[-1])
 ef=float(bars.factor.iloc[0]);lastf=ef;accrued=1.;oldbe=trailing.BREAKEVEN_GAIN
 trailing.BREAKEVEN_GAIN=dec(.08 if mode=='close' else .05)
 try:
  for i,(d,b) in enumerate(bars.iterrows()):
   f=float(b.factor);ratio=f/lastf;stop/=ratio;ep/=ratio;accrued=f/ef;lastf=f
   if pending:day=d;xraw=float(b.o);why='close_stop';break
   if i or entry_low:
    line=stop*(.95 if mode=='close' else 1.)
    if b.l<=line:day=d;xraw=min(float(b.o),line) if i else line;why='disaster' if mode=='close' else 'touch';break
   ma=b.ma20_economic_prior/f
   mark=b.c if timing=='close' else b.h
   prop=trailing.next_stop(phase='initial',entry_price=dec(ep),current_stop=dec(stop),last_price=dec(mark),
      ma20=dec(ma) if pd.notna(ma) else None,initial_stop_price=dec(initial/accrued),regime_is_defensive=defensive)
   if prop is not None:stop=float(prop)
   if mode=='close' and b.c<stop:pending=True
   day=d;xraw=float(b.c)
  else:
   if horizon and len(bars)>=horizon:why='horizon'
 finally:trailing.BREAKEVEN_GAIN=oldbe
 entry=float(entry_override or row.entry);xp=xraw*accrued
 return dict(id=row.id,s=row.s,ed=row.ed,xd=day,entry=entry,xp=xp,exit_raw=xraw,
    share_factor=accrued,stop=initial,qty_actual=row.qty,actual_pnl=row.pnl,
    stop_pct=(1-initial/entry)*100,missing_stop=False,old_stop_missing=bool(pd.isna(row.isl)),
    ret=(xp*.995/entry-1)*100,why=why)

def make_rows(missing='5pct',**opts):
 rows=[];unresolved=[]
 for r in S.itertuples():
  if pd.notna(r.isl):stop=float(r.isl);basis='recorded initial stop'
  elif missing=='structural':
   stop=E.loc[r.id,'new_stop'];basis='calculated new stop from prior bars'
  elif missing=='reject':stop=np.nan;basis='unknown'
  else:stop=r.entry*(1-float(missing.removesuffix('pct'))/100);basis='assumed '+missing+' because original unknown'
  if pd.isna(stop) or not 0<stop<r.entry:
   unresolved.append(dict(id=r.id,s=r.s,ed=r.ed,src=r.src,decision='no usable initial stop'));continue
  x=outcome(r,stop,**opts)
  if x:
   x.update(src=r.src,stop_basis=basis,old_stop_missing=bool(pd.isna(r.isl)),actual_exit_date=r.xd,actual_exit_price=r.exitp)
   rows.append(x)
 return rows,unresolved

def book(rows,unresolved=(),fee=.0025,slip=.005,seed=None,allow_duplicate=False,cap=500000):
 rng=np.random.default_rng(seed if seed is not None else 0)
 candidates=[dict(r,tie=r['id'] if seed is None else float(rng.random())) for r in rows]
 candidates.sort(key=lambda r:(r['ed'],r['tie']))
 cash=6000000.;held=[];taken=[];decisions=list(unresolved)
 for r in candidates:
  for h in held[:]:
   if h['why']!='open@end' and (h['xd']<r['ed'] or (h['xd']==r['ed'] and h['why']=='close_stop')):
    cash+=h['deploy']+h['net']+h['cost'];held.remove(h)
  qty=int(cap/r['entry']);deploy=qty*r['entry'];cost=deploy*fee
  reason='taken'
  if not allow_duplicate and any(h['s']==r['s'] for h in held):reason='same stock already held'
  elif len(held)>=12:reason='12 occupied slots'
  elif deploy+cost>cash+1e-6:reason='cash unavailable at entry including costs'
  decisions.append(dict(id=r['id'],s=r['s'],ed=r['ed'],src=r['src'],decision=reason,stop_basis=r['stop_basis'],cash_before=cash))
  if reason!='taken':continue
  x=dict(r,qty=qty,deploy=deploy,cost=cost,net=qty*(r['xp']*(1-slip)-r['entry'])-cost)
  cash-=deploy+cost;held.append(x);taken.append(x)
  assert cash>=-1e-5 and len(held)<=12 and x['deploy']<=cap+.01
  assert allow_duplicate or len(set(h['s'] for h in held))==len(held)
 t=pd.DataFrame(taken);d=pd.DataFrame(decisions)
 assert len(d)==132 and d.id.nunique()==132
 if not len(t):return dict(n=0,total=0,closed=0,open=0,open_n=0),t,d
 op=t.why.eq('open@end')
 st=dict(n=len(t),total=t.net.sum(),closed=t.loc[~op,'net'].sum(),open=t.loc[op,'net'].sum(),open_n=int(op.sum()),
    closed_win_pct=(t.loc[~op,'net']>0).mean()*100,old_missing_taken=int(t.old_stop_missing.sum()),
    reasons=d[d.decision!='taken'].decision.value_counts().to_dict())
 return st,t,d

cases=[('baseline_5pct','5pct',{},{}),('missing_3pct','3pct',{},{}),('missing_8pct','8pct',{},{}),('missing_10pct','10pct',{},{}),
 ('missing_structural','structural',{},{}),('known_stops_only','reject',{},{}),
 ('research_60session','5pct',dict(horizon=60),{}),('high_sampled','5pct',dict(timing='high'),{}),
 ('always_defensive','5pct',dict(defensive=True),{}),('adverse_entry_day','5pct',dict(entry_low=True),{}),
 ('zero_costs','5pct',{},dict(fee=0,slip=0)),('old_exit_control','5pct',dict(mode='touch'),{}),
 ('allow_separate_same_stock_lots','5pct',{},dict(allow_duplicate=True))]
results=[];ledgers={};decisions={};cache={}
for name,missing,opts,bopts in cases:
 rows,u=make_rows(missing,**opts);cache[name]=(rows,u)
 st,t,d=book(rows,u,**bopts);results.append(dict(scenario=name,**st));ledgers[name]=t;decisions[name]=d
 t.to_csv(P/(name+'_trades.csv'),index=False);d.to_csv(P/(name+'_decisions.csv'),index=False)
R=pd.DataFrame(results);R.drop(columns='reasons').to_csv(P/'scenario_summary.csv',index=False)
base=ledgers['baseline_5pct'];old=ledgers['old_exit_control']
orders=[]
for seed in range(500):
 n,_,_=book(*cache['baseline_5pct'],seed=seed);o,_,_=book(*cache['old_exit_control'],seed=seed)
 orders.append(dict(seed=seed,new=n['total'],old=o['total'],difference=n['total']-o['total']))
O=pd.DataFrame(orders);O.to_csv(P/'500_orders.csv',index=False)
for label,seed in [('highest',int(O.loc[O.new.idxmax(),'seed'])),('median_example',int(O.loc[(O.new-O.new.median()).abs().idxmin(),'seed']))]:
 st,t,d=book(*cache['baseline_5pct'],seed=seed)
 t.to_csv(P/(label+'_trades.csv'),index=False);d.to_csv(P/(label+'_decisions.csv'),index=False)
 results.append(dict(scenario=label+'_entry_order',seed=seed,**st))
source_rows=[]
for src,g in S.groupby('src'):
 t=base[base.src==src];op=t.why.eq('open@end')
 source_rows.append(dict(source=src,opportunities=len(g),executed=len(t),closed=t.loc[~op,'net'].sum(),open=t.loc[op,'net'].sum(),total=t.net.sum()))
B=pd.DataFrame(source_rows);B.to_csv(P/'strategy_source_breakdown.csv',index=False)
ledger=S[['id','s','src','ed','entry','qty','xd','pnl','isl']].rename(columns={'qty':'actual_qty','xd':'actual_exit_date','pnl':'actual_pnl','isl':'recorded_initial_stop'})
ledger=ledger.merge(decisions['baseline_5pct'][['id','decision','stop_basis']],on='id',how='left')
ledger=ledger.merge(base[['id','qty','stop','xd','why','net']].rename(columns={'qty':'new_qty','stop':'modeled_stop','xd':'new_exit_or_mark_date','why':'exit_reason','net':'new_net_pnl'}),on='id',how='left')
ledger.to_csv(P/'all_132.csv',index=False)
# Independent counterfactual totals must not be confused with funded results.
allrows=cache['baseline_5pct'][0]
independent=sum(int(500000/r['entry'])*(r['xp']*.995-r['entry'])-int(500000/r['entry'])*r['entry']*.0025 for r in allrows)
# End-of-day marked equity in split-consistent units.
daily=[]
for day in sorted({d for r in allrows for d in frames[r['s']].loc[S.ed.min():ns['END']].index}):
 entered=base[base.ed<=day];closed=entered[(entered.xd<=day)&(entered.why!='open@end')];active=entered.drop(closed.index)
 value=6000000+closed.net.sum()
 for r in active.itertuples():
  f=frames[r.s];ef=f.loc[f.index>=r.ed,'factor'].iloc[0];b=f.loc[:day].iloc[-1]
  mark=b.c*b.factor/ef
  value+=r.qty*(mark*.995-r.entry)-r.cost
 daily.append(dict(date=day,equity=value,positions=len(active)))
D=pd.DataFrame(daily);D['drawdown']=D.equity-D.equity.cummax().clip(lower=6000000)
D.to_csv(P/'daily_equity.csv',index=False)
assert abs(D.equity.iloc[-1]-6000000-base.net.sum())<.01
assert sum(B.opportunities)==132 and abs(B.total.sum()-base.net.sum())<.01
assert (base.qty==np.floor(500000/base.entry)).all()
summary=dict(baseline=results[0],assumption_results=results,
    order_range=[O.new.min(),O.new.median(),O.new.max()],orders_at_least_21L=int((O.new>=2100000).sum()),
    median_new_minus_old=O.difference.median(),drawdown=D.drawdown.min(),unfunded_total=independent,
    contract={'capital':6000000,'per_trade_cap':500000,'slots':12,'opportunities':132,'new_entry_gates':False,'historical_buy_dates_prices':True,'source_strategy_preserved':True,'horizon':'through 22 September cutoff, no artificial time exit','baseline_missing_stop':'5% only as explicit research assumption','fee':.0025,'exit_slippage':.005})
(P/'summary.json').write_text(json.dumps(summary,indent=2,default=str))
print(json.dumps(summary,indent=2,default=str))
