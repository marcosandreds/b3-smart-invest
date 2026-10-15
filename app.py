from pathlib import Path
import json
import pandas as pd
import streamlit as st
from engine import ranking,indicators,position,backtest
st.set_page_config(page_title='B3 Smart Invest',layout='wide')
st.title('B3 Smart Invest')
st.caption('Pesquisa e simulação • Dados diários • Não executa ordens')
root=Path(__file__).parent
st.warning('Ações não garantem renda mensal. Scores são regras experimentais; stops podem sofrer gaps. Dados demonstrativos não representam oportunidades reais.')
mode=st.sidebar.radio('Dados',['Demonstração','Coleta real'])
base=root/'data';file=base/('demo_prices.parquet' if mode=='Demonstração' else 'prices.parquet')
if not file.exists():st.info('Execute python collect.py no GitHub Actions para gerar a primeira coleta.');st.stop()
p=pd.read_parquet(file);cfg=json.loads((root/'config.json').read_text())
fpath=base/('demo_fundamentals.csv' if mode=='Demonstração' else 'fundamentals.csv')
f=pd.read_csv(fpath) if fpath.exists() else pd.DataFrame()
if mode=='Demonstração':st.error('DADOS SINTÉTICOS — somente para testar a interface.')
else:
    if (base/'status.json').exists():st.json(json.loads((base/'status.json').read_text()),expanded=False)
    st.caption(f'Último pregão nos arquivos: {p.Date.max():%d/%m/%Y}. Confirme atualização antes de usar.')
weights=[st.sidebar.slider(n,0,100,v) for n,v in zip(['Fundamental','Técnico','Risco'],[50,30,20])]
if sum(weights)==0:st.error('Selecione algum peso.');st.stop()
minimum=st.sidebar.number_input('Liquidez média mínima (R$)',0,100000000,5000000,1000000)
upload=st.sidebar.file_uploader('Fundamentos CSV revisados',type='csv')
if upload:f=pd.read_csv(upload)
try:r=ranking(p[p.ticker!='^BVSP'],f,weights,minimum)
except ValueError as ex:st.error(str(ex));st.stop()
a,b,c,d=st.tabs(['Ranking','Análise','Backtest','Posição e renda'])
with a:
    st.caption('Sem cobertura fundamental suficiente, o score final fica indisponível. A lista inicial é configurável e não é um ranking oficial de liquidez da B3.')
    st.dataframe(r,use_container_width=True);st.download_button('Exportar ranking',r.to_csv(index=False).encode(),'ranking.csv')
if r.empty:st.stop()
ticker=st.sidebar.selectbox('Ação',r.ticker)
x=indicators(p[p.ticker==ticker].set_index('Date'))
with b:
    st.subheader(ticker);st.line_chart(x[['Close','ma20','ma50','ma200']]);st.line_chart(x[['rsi']]);st.dataframe(r[r.ticker==ticker])
with c:
    st.info('Backtest técnico por ação. Não valida o score fundamental, nem uma carteira conjunta. Universo atual implica viés de sobrevivência. Preços ajustados; não contabiliza proventos separadamente ou tributos.')
    cost=st.number_input('Custo e slippage por lado (%)',0.,5.,.1,.05)/100
    equity,trades=backtest(x[['Open','High','Low','Close','Volume']],cost)
    if not equity.empty:
        ret=equity.equity.pct_change().dropna();dd=equity.equity/equity.equity.cummax()-1
        days=(equity.index[-1]-equity.index[0]).days
        st.write({'Retorno':equity.equity.iloc[-1]/10000-1,'CAGR':(equity.equity.iloc[-1]/10000)**(365/max(days,1))-1,'Drawdown':dd.min(),'Operações encerradas':len(trades)})
        st.line_chart(equity);st.dataframe(trades)
        monthly=equity.equity.resample('ME').last().pct_change().dropna()
        st.bar_chart(monthly);st.download_button('Exportar curva',equity.to_csv().encode(),'backtest.csv')
with d:
    cap=st.number_input('Capital de referência (R$)',100.,100000000.,100000.,1000.)
    cash=st.number_input('Caixa disponível (R$)',0.,100000000.,100000.,1000.)
    risk=st.slider('Risco teórico por operação (%)',.1,2.,.75,.05)/100
    weight=st.slider('Limite por ação (%)',1,30,10)/100
    st.write(position(cap,float(x.Close.iloc[-1]),float(x.atr.iloc[-1]),risk,weight,cash))
    st.caption('Valores usam preços ajustados da fonte e exigem conferência da cotação negociável. Risco real pode exceder o calculado. O limite setorial exige considerar as demais posições.')
    withdrawal=st.number_input('Retirada mensal desejada (R$)',0.,1000000.,1000.,100.)
    st.write(f'Retirada anual pretendida / capital: {12*withdrawal/cap:.1%}')
    st.caption('Essa razão não é previsão de retorno. A curva mensal do backtest mostra a irregularidade dos resultados. A primeira versão não mantém livro de operações ou apuração tributária.')
