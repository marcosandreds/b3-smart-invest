import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import pandas as pd
from engine import position,fundamental_scores,backtest

def test_position_limits():
    p=position(100000,25,.8,cash=2000)
    assert p['quantity']==80 and p['risk']<=750 and p['value']<=2000

def test_future_fundamentals_excluded():
    f=pd.DataFrame([dict(ticker='A',sector='X',published_at='2030-01-01',roe=.1,operating_margin=.1,revenue_growth=.1,earnings_growth=.1,fcf_yield=.1,net_debt_ebitda=1,pe=10)])
    assert fundamental_scores(f,'2026-01-01').empty

def test_cash_when_no_signal():
    index=pd.bdate_range('2020-01-01',periods=300)
    f=pd.DataFrame(dict(Open=10,High=10,Low=10,Close=10,Volume=1000000),index=index)
    e,t=backtest(f)
    assert (e.equity==10000).all() and t.empty

def test_scores_and_coverage():
    rows=[]
    for i in range(3):
        rows.append(dict(ticker=str(i),sector='X',published_at='2026-08-01',roe=i+.1,operating_margin=i+.1,revenue_growth=i+.1,earnings_growth=i+.1,fcf_yield=i+.1,net_debt_ebitda=3-i,pe=15-i))
    s=fundamental_scores(pd.DataFrame(rows),'2026-09-01')
    assert s.iloc[-1].fundamental==100 and (s.coverage==100).all()
    assert fundamental_scores(pd.DataFrame(rows),'2027-09-01').fundamental.isna().all()
