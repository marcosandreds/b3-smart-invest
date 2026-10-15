"""Snapshots Yahoo atuais. Não substitui normalização CVM ou histórico point-in-time."""
from pathlib import Path
import json,time
import pandas as pd
import yfinance as yf
ROOT=Path(__file__).parent

def main():
    status=ROOT/'data/fundamentals_status.json'
    if status.exists():
        last=pd.Timestamp(json.loads(status.read_text())['observed_at'])
        if (pd.Timestamp.now().normalize()-last).days<7:
            print('Snapshot semanal ainda válido.');return
    records=[];errors=[]
    now=pd.Timestamp.now(tz='UTC').tz_localize(None).normalize()
    path=ROOT/'data/fundamentals.csv'
    old=pd.read_csv(path) if path.exists() else pd.DataFrame()
    for ticker in json.loads((ROOT/'config.json').read_text())['tickers']:
        try:
            a=yf.Ticker(ticker+'.SA').info
            sector=a.get('sector');market=a.get('marketCap');ebitda=a.get('ebitda')
            if not sector:raise ValueError('Setor ausente')
            # Múltiplos industriais não devem ser impostos a instituições financeiras.
            if sector=='Financial Services':raise ValueError('Setor financeiro exige modelo específico')
            debt=a.get('totalDebt');cash=a.get('totalCash');fcf=a.get('freeCashflow')
            records.append(dict(ticker=ticker,sector=sector,published_at=str(now.date()),
                roe=a.get('returnOnEquity'),operating_margin=a.get('operatingMargins'),
                revenue_growth=a.get('revenueGrowth'),earnings_growth=a.get('earningsGrowth'),
                fcf_yield=fcf/market if fcf is not None and market and market>0 else None,
                net_debt_ebitda=(debt-cash)/ebitda if debt is not None and cash is not None and ebitda and ebitda>0 else None,
                pe=a.get('trailingPE'),source='Yahoo snapshot',observed_at=now.isoformat()))
        except Exception as ex:errors.append(dict(ticker=ticker,error=str(ex)))
        time.sleep(.2)
    if records:
        combined=pd.concat([old,pd.DataFrame(records)],ignore_index=True)
        combined.drop_duplicates(['ticker','published_at'],keep='last').to_csv(path,index=False)
    (ROOT/'data/fundamentals_status.json').write_text(json.dumps({'observed_at':now.isoformat(),'records':len(records),'errors':errors},indent=2))
    if not records and old.empty:raise RuntimeError('Sem fundamentos; ranking continuará bloqueado.')
if __name__=='__main__':main()
