# B3 Smart Invest — versão inicial 1.0

Pacote de pesquisa em Python/Streamlit. Não é robô de execução e não promete renda mensal.

## Implantar sem servidor próprio
1. Crie um repositório no GitHub e envie **o conteúdo** desta pasta, incluindo `.github/workflows/daily.yml`. A pasta oculta contém a automação: o envio pelo navegador pode exigir criar o arquivo manualmente com esse caminho.
2. Em Settings → Actions → General, habilite workflows e permissões de leitura/escrita. Proteção de branch pode impedir o commit automático: nesse caso use branch de dados ou ajuste as regras do seu projeto.
3. Abra Actions → Atualizar dados B3 → Run workflow. A primeira coleta baixa dez anos da lista configurada; pode haver falhas individuais da fonte. Consulte `data/status.json`.
4. Acesse https://share.streamlit.io, conecte GitHub, escolha o repositório, branch e `app.py`, Python 3.11, e faça o deploy.
5. O painel abre em DEMONSTRAÇÃO. Selecione Coleta real depois de concluir a coleta. O disparo manual também tenta coletar fundamentos Yahoo atuais. Lacunas ou cobertura insuficiente bloqueiam score final. Revise os dados antes de usar.
6. O cron está em UTC: 22:37 corresponde a 19:37 em São Paulo, de segunda a sexta. Não conhece feriados. Execuções podem atrasar. Repositórios públicos inativos podem ter agendamento desabilitado; acompanhe o histórico de Actions.

Planos gratuitos têm limites e podem mudar. Não há assinatura ou credencial paga exigida pelo pacote; confirme as condições atuais dos serviços. Repositório público expõe código e dados: não inclua sua carteira pessoal ou segredos.

## Executar localmente
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python collect.py
streamlit run app.py
```

## Arquitetura e arquivos
`collect.py`: Yahoo/yfinance → OHLCV ajustado → `data/prices.parquet` → ranking.
`engine.py`: indicadores, scores, dimensionamento e backtest.
`app.py`: ranking, análise, backtest e simulação de retirada.
`config.json`: universo candidato, liquidez mínima, pesos e piso fundamental.
`data/demo_*`: dados sintéticos reproduzíveis, identificados explicitamente.
`data/fundamentals_template.csv`: contrato para fundamentos revisados.
`tests/`: verificações de limites, ausência de sinais e exclusão de informações futuras.

A lista é uma seleção inicial de candidatos, não uma afirmação de quais são hoje as 50 ações mais líquidas. O filtro usa volume financeiro médio estimado em 20 pregões, com preços ajustados. Revise tickers em config.json; alterações societárias podem gerar códigos inválidos. A versão não descobre automaticamente todas as ações da B3.

## Fórmula do score
F,T,R de 0 a 100. Score = (pesoF×F + pesoT×T + pesoR×R)/soma dos pesos.
Padrão 50/30/20. Piso F=60; candidata exige score≥75 e pullback ou breakout.
Fundamentos: ROE 15, margem operacional 10, crescimento receita 10, crescimento lucro 10, FCF yield 20, dívida líquida/EBITDA 15, P/L 20. Percentis dentro do setor; menor dívida e P/L recebem maior nota. Setor precisa de ao menos 3 valores válidos por indicador. Cobertura abaixo de 80% ou publicação com mais de 180 dias bloqueia F. Dados faltantes não são redistribuídos. O score é uma hipótese a validar, não probabilidade de ganho.
Técnico: preço>MM200 30; MM50>MM200 25; MM20>MM50 15; MM200 ascendente 10; RSI45–65 10; volume>1,2×média anterior 10.
Risco: volatilidade 60 dias 50; queda em relação à máxima 252 pregões 30; liquidez 20. Escalas fixas no engine.py. Correlação, beta e concentração de carteira ainda não fazem parte deste score.
Pullback: tendência positiva, RSI anterior 40–50 e recuperação. Breakout: fechamento supera máxima dos 20 dias anteriores, volume>1,5×média anterior e preço>MM200.

## Fundamentos: caminho rigoroso para CVM
A CVM disponibiliza DFP/ITR em https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp e https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr.
**Esta versão não implementa coleta e normalização automática da CVM.** A base requer ligação ticker↔CNPJ/CD_CVM, escolha consolidado/individual, escalas, reapresentações, contas setoriais e número de ações para valuation. Não há EBITDA ou ROIC genérico confiável calculado automaticamente. Não trate bancos e seguradoras como empresas industriais.
Para usar agora: copie o template para `data/fundamentals.csv`, preencha indicadores revisados e faça commit ou envie CSV pelo painel. `published_at` é a data em que a informação passou a ser pública, não encerramento do trimestre. ROE, margens, crescimentos e FCF yield em decimal (.15=15%). P/L e dívida/EBITDA em múltiplos. Todos os indicadores devem refletir a mesma base temporal (preferencialmente últimos 12 meses) e informações disponíveis na data. Setor deve ser comparável; financeiro exige modelo específico e não deve receber estes múltiplos inadequados.

## Backtest e limites
A primeira versão testa SOMENTE a regra técnica por ação, com execução na abertura seguinte, custo/slippage por lado, stop 2×ATR, saída abaixo da MM50 e execução de gap no preço de abertura. Usa preços ajustados; não soma dividendos outra vez. Não valida pesos fundamentalistas ou carteira conjunta. Não há otimização/walk-forward, impostos, taxa livre de risco, livro da carteira, alertas ou integração de corretora nesta entrega. Operações abertas ficam marcadas a mercado. A estimativa de liquidez histórica com preços ajustados é aproximada.
A seleção por universo atual introduz sobrevivência; reapresentações e séries ajustadas exigem cuidado para backtests completos. Para avançar, construir base point-in-time e universo histórico, separar treino/teste, executar carteira com caixa e limites de exposição, comparar IBOV/CDI e tratar tributos. O pacote não apresenta números históricos de rentabilidade fictícios como resultados reais.

## Dimensionamento e renda
Quantidade = mínimo entre orçamento de risco/(2×ATR), limite por ação/preço e caixa/preço. Preço e ATR ajustados exigem conferir cotação atual antes de qualquer decisão. Stops não limitam perfeitamente perdas em gaps. O painel mostra retirada anual pretendida/capital; não prevê renda. Reserva de despesas deve ser definida fora das ações.

## Fontes técnicas
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
https://github.com/ranaroussi/yfinance — fonte não oficial da B3, sujeita a disponibilidade e termos de uso.

## Coleta fundamental auxiliar implementada
`python fundamentals.py` coleta snapshots atuais do Yahoo (ROE, margens, crescimentos, FCF yield, dívida/EBITDA e P/L), com data de observação registrada e relatório de falhas. O workflow verifica diariamente a idade do snapshot e tenta renová-lo a cada sete dias. `published_at` nesses snapshots é a data em que nosso sistema observou a informação, uma aproximação conservadora para uso a partir desse dia — não a data original do balanço. Não há reconstrução do passado. Dados do Yahoo podem usar bases temporais diferentes e precisam de revisão. Bancos/seguradoras são bloqueados pelo setor financeiro. CSV revisado pode substituir/complementar a base. A integração CVM permanece pendente.
