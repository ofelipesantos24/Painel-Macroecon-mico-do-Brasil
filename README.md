# 📊 Painel Macroeconômico do Brasil

Dashboard web em **Python + Pandas** com gráficos interativos (Plotly) e indicadores
calculados a partir de **dados públicos** do Banco Central do Brasil (API SGS, sem chave).

## Indicadores
| Série | Código SGS | Descrição |
|---|---|---|
| IPCA | 433 | Variação mensal da inflação (%) |
| Selic | 4390 | Selic acumulada no mês (%) |
| Desemprego | 24369 | Taxa de desocupação — PNAD Contínua (%) |
| Dólar | 1 | Dólar comercial (venda), média mensal (R$) |

**Derivados (Pandas):** IPCA e Selic acumulados em 12 meses, juro real ex-post
`(1+Selic12m)/(1+IPCA12m)-1`, variação anual do dólar, base 100, correlações.

## Como rodar
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
pytest                                              # testes dos cálculos
```
Abre em http://localhost:8501.

## Estrutura
```
app.py                # interface (Streamlit + Plotly)
src/data.py           # coleta da API, cache local e fallback offline
src/indicators.py     # cálculos com Pandas
tests/                # testes unitários
data/cache.csv        # gerado automaticamente após a 1ª coleta
```

## Comportamento de dados
1. Baixa da API do BCB → 2. se falhar, usa `data/cache.csv` → 3. sem cache, usa **dados fictícios** (aviso na tela).

## Ideias de evolução
- Adicionar séries (PIB, IBC-Br, Focus, IGP-M) — basta incluir o código em `SERIES`.
- Dados regionais do IBGE (API SIDRA) com mapa coroplético.
- Deploy gratuito no Streamlit Community Cloud.
- Alertas: destacar quando o IPCA 12m ultrapassar o teto da meta.
