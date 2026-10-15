import json
from pathlib import Path
import pandas as pd
import yfinance as yf
from engine import ranking
ROOT=Path(__file__).parent

def main():
    cfg=json.loads((ROOT/'config.json').read_text());frames=[];errors=[]
    for t in cfg['tickers']+['^BVSP']:
        try:
            d=yf.download(t if t.startswith('^') else t+'.SA',period='10y',auto_adjust=True,progress=False,threads=False)
            if isinstance(d.columns,pd.MultiIndex):d.columns=d.columns.get_level_values(0)
            d=d.dropna(subset=['Open','High','Low','Close']);d.index=pd.to_datetime(d.index).tz_localize(None)
            if len(d)<220:raise ValueError('Histórico insuficiente')
            d=d.reset_index();d['ticker']=t;frames.append(d)
        except Exception as exc:errors.append({'ticker':t,'error':str(exc)})
    if not frames:raise RuntimeError('Nenhuma cotação obtida. Arquivos anteriores preservados.')
    prices=pd.concat(frames,ignore_index=True)
    path=ROOT/'data/fundamentals.csv';f=pd.read_csv(path) if path.exists() else pd.DataFrame()
    r=ranking(prices[prices.ticker!='^BVSP'],f,cfg['weights'],cfg['min_daily_value'],cfg['fundamental_floor'])
    prices.to_parquet(ROOT/'data/prices.parquet',index=False);r.to_parquet(ROOT/'data/ranking.parquet',index=False)
    (ROOT/'data/status.json').write_text(json.dumps({'updated_at':pd.Timestamp.now(tz='UTC').isoformat(),'errors':errors},indent=2))
    print(f'{len(r)} ações elegíveis; {len(errors)} falhas. Consulte data/status.json.')
if __name__=='__main__':main()
