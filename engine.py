import numpy as np
import pandas as pd

METRICS={'roe':(1,15),'operating_margin':(1,10),'revenue_growth':(1,10),
'earnings_growth':(1,10),'fcf_yield':(1,20),'net_debt_ebitda':(-1,15),'pe':(-1,20)}

def indicators(df):
    d=df.copy().sort_index(); c=d.Close
    for n in [20,50,200]: d[f'ma{n}']=c.rolling(n).mean()
    delta=c.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    d['rsi']=100-100/(1+gain/loss.replace(0,np.nan))
    d.loc[(loss==0)&(gain>0),'rsi']=100
    tr=pd.concat([d.High-d.Low,(d.High-c.shift()).abs(),(d.Low-c.shift()).abs()],axis=1).max(axis=1)
    d['atr']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    d['value20']=(c*d.Volume).rolling(20).mean()
    d['vol']=c.pct_change().rolling(60).std()*np.sqrt(252)
    d['drawdown']=c/c.rolling(252,min_periods=60).max()-1
    d['volume_ratio']=d.Volume/d.Volume.rolling(20).mean().shift(1)
    d['resistance']=d.High.rolling(20).max().shift(1)
    d['pullback']=(c>d.ma200)&(d.ma50>d.ma200)&(d.rsi.shift(1).between(40,50))&(d.rsi>d.rsi.shift(1))
    d['breakout']=(c>d.ma200)&(c>d.resistance)&(d.volume_ratio>1.5)
    d['technical']=((c>d.ma200)*30+(d.ma50>d.ma200)*25+(d.ma20>d.ma50)*15+
        (d.ma200>d.ma200.shift(20))*10+d.rsi.between(45,65)*10+(d.volume_ratio>1.2)*10)
    d['risk']=((1-d.vol/.6).clip(0,1)*50+(1+d.drawdown/.5).clip(0,1)*30+(d.value20/20000000).clip(0,1)*20)
    return d

def fundamental_scores(f,asof):
    cols=['ticker','sector','published_at',*METRICS]
    if not set(cols).issubset(f.columns): raise ValueError('CSV fundamental incompleto: '+', '.join(cols))
    f=f.copy(); f['published_at']=pd.to_datetime(f.published_at,errors='coerce')
    f=f[f.published_at<=pd.Timestamp(asof)].sort_values('published_at').drop_duplicates('ticker',keep='last')
    for m in METRICS: f[m]=pd.to_numeric(f[m],errors='coerce')
    f.loc[f.pe<=0,'pe']=np.nan
    f['fundamental']=0.; f['coverage']=0.
    for m,(direction,weight) in METRICS.items():
        counts=f.groupby('sector')[m].transform('count')
        ranked=f.groupby('sector')[m].rank(pct=True,ascending=direction==1)
        # Setores pequenos não fornecem comparação confiável.
        valid=f[m].notna()&(counts>=3)
        f['fundamental']+=ranked.where(valid,0)*weight
        f['coverage']+=valid*weight
    f.loc[f.coverage<80,'fundamental']=np.nan
    f.loc[(pd.Timestamp(asof)-f.published_at).dt.days>180,'fundamental']=np.nan
    return f

def ranking(prices,f,weights=(50,30,20),minimum=5000000,floor=60):
    rows=[]
    for ticker,g in prices.groupby('ticker'):
        d=indicators(g.set_index('Date')); a=d.iloc[-1]
        if len(d)<220 or a.value20<minimum: continue
        rows.append(dict(ticker=ticker,date=d.index[-1],price=a.Close,technical=a.technical,risk=a.risk,atr=a.atr,
                         liquidity=a.value20,trigger=bool(a.pullback or a.breakout)))
    r=pd.DataFrame(rows)
    if r.empty:return r
    if f.empty:r['fundamental']=np.nan;r['coverage']=0
    else:r=r.merge(fundamental_scores(f,r.date.max())[['ticker','fundamental','coverage']],on='ticker',how='left')
    ws=np.asarray(weights)/sum(weights)
    r['score']=r.fundamental*ws[0]+r.technical*ws[1]+r.risk*ws[2]
    r['signal']=np.where(r.fundamental.isna(),'Fundamentos pendentes',np.where((r.fundamental>=floor)&r.trigger&(r.score>=75),'Candidata','Observar'))
    return r.sort_values(['score','technical'],ascending=False,na_position='last')

def position(capital,entry,atr,risk_pct=.0075,max_weight=.1,cash=None):
    if capital<=0 or entry<=0 or atr<=0:return dict(quantity=0,stop=0,risk=0,value=0)
    distance=2*atr; stop=entry-distance
    if stop<=0:return dict(quantity=0,stop=stop,risk=0,value=0)
    q=max(0,int(min(capital*risk_pct/distance,capital*max_weight/entry,(capital if cash is None else cash)/entry)))
    return dict(quantity=q,stop=stop,risk=q*distance,value=q*entry)

def backtest(df,cost=.001,initial=10000):
    # Técnico apenas: sinal no fechamento, execução na abertura seguinte.
    d=indicators(df); cash=initial;q=0;stop=0;records=[];trades=[];entry_cost=0
    for i in range(220,len(d)):
        day=d.iloc[i];prev=d.iloc[i-1];date=d.index[i]
        if q:
            exit_price=None
            if day.Open<=stop:exit_price=day.Open
            elif day.Low<=stop:exit_price=stop
            elif prev.Close<prev.ma50:exit_price=day.Open
            if exit_price is not None:
                proceeds=q*exit_price*(1-cost);cash+=proceeds
                trades.append(dict(date=date,pnl=proceeds-entry_cost));q=0
        elif prev.pullback or prev.breakout:
            size=position(cash,day.Open,prev.atr,max_weight=.95,cash=cash/(1+cost))
            q=size['quantity'];stop=size['stop'];entry_cost=q*day.Open*(1+cost);cash-=entry_cost
            if q and day.Low<=stop:
                proceeds=q*stop*(1-cost);cash+=proceeds;trades.append(dict(date=date,pnl=proceeds-entry_cost));q=0
        records.append(dict(date=date,equity=cash+q*day.Close))
    e=pd.DataFrame(records).set_index('date') if records else pd.DataFrame(columns=['equity'])
    return e,pd.DataFrame(trades)
