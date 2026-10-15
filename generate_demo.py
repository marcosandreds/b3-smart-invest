from pathlib import Path
import numpy as np
import pandas as pd
p=Path(__file__).parent/'data';rng=np.random.default_rng(42);frames=[];fund=[]
dates=pd.bdate_range('2021-01-01','2026-09-30')
for i,t in enumerate(['DEMO1','DEMO2','DEMO3','DEMO4','DEMO5','DEMO6']):
    c=20*np.exp(np.cumsum(rng.normal(.0004,.013,len(dates))))
    o=np.r_[c[0],c[:-1]]*np.exp(rng.normal(0,.003,len(c)))
    frames.append(pd.DataFrame(dict(Date=dates,Open=o,High=np.maximum(o,c)*1.01,Low=np.minimum(o,c)*.99,Close=c,Volume=rng.integers(1000000,3000000,len(c)),ticker=t)))
    fund.append(dict(ticker=t,sector='Demonstração',published_at='2026-08-01',roe=.08+i*.025,operating_margin=.1+i*.02,revenue_growth=.02+i*.01,earnings_growth=.03+i*.01,fcf_yield=.04+i*.01,net_debt_ebitda=3-i*.3,pe=20-i*2))
pd.concat(frames).to_parquet(p/'demo_prices.parquet',index=False)
pd.DataFrame(fund).to_csv(p/'demo_fundamentals.csv',index=False)
