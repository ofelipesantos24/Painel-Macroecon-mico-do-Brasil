"""Dashboard Macroeconômico Brasil — Streamlit + Pandas + Plotly.

Executar:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data import load_data
from src.indicators import base_100, enrich, kpis, resumo_estatistico

st.set_page_config(page_title="Painel Macro Brasil", page_icon="📊", layout="wide")

LABELS = {
    "IPCA": "IPCA mensal (%)",
    "IPCA_12m": "IPCA acumulado 12m (%)",
    "Selic": "Selic mensal (%)",
    "Selic_12m": "Selic acumulada 12m (%)",
    "Juro_real": "Juro real ex-post (%)",
    "Desemprego": "Desemprego (%)",
    "Dolar": "Dólar médio (R$)",
    "Dolar_var_12m": "Dólar var. 12m (%)",
}


@st.cache_data(ttl=6 * 3600, show_spinner="Baixando dados do Banco Central...")
def get_data(start_year: int):
    df, origem = load_data(start_year)
    return enrich(df), origem


# ---------- Sidebar ----------
st.sidebar.title("⚙️ Filtros")
start_year = st.sidebar.slider("Baixar dados desde", 2010, 2022, 2015)
df_all, origem = get_data(start_year)

dmin, dmax = df_all.index.min().date(), df_all.index.max().date()
periodo = st.sidebar.date_input("Período", (dmin, dmax), min_value=dmin, max_value=dmax)
if isinstance(periodo, tuple) and len(periodo) == 2:
    df = df_all.loc[pd.Timestamp(periodo[0]):pd.Timestamp(periodo[1])]
else:
    df = df_all

if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

# ---------- Cabeçalho ----------
st.title("📊 Painel Macroeconômico do Brasil")
st.caption("Fonte: Banco Central do Brasil — API SGS (dados abertos).")

if origem == "sintetico":
    st.warning("Sem acesso à API e sem cache local: exibindo **dados fictícios** apenas para demonstração.")
elif origem == "cache":
    st.info("Sem acesso à API: exibindo o último **cache local** salvo.")

if df.empty:
    st.error("Nenhum dado no período selecionado.")
    st.stop()

# ---------- KPIs ----------
k = kpis(df)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("IPCA 12m", f"{k['IPCA_12m']['valor']:.2f}%", f"{k['IPCA_12m']['delta']:+.2f} p.p.", delta_color="inverse")
c2.metric("Selic 12m", f"{k['Selic_12m']['valor']:.2f}%", f"{k['Selic_12m']['delta']:+.2f} p.p.", delta_color="off")
c3.metric("Juro real", f"{k['Juro_real']['valor']:.2f}%", f"{k['Juro_real']['delta']:+.2f} p.p.", delta_color="off")
c4.metric("Desemprego", f"{k['Desemprego']['valor']:.1f}%", f"{k['Desemprego']['delta']:+.1f} p.p.", delta_color="inverse")
c5.metric("Dólar (média)", f"R$ {k['Dolar']['valor']:.2f}", f"{k['Dolar']['delta']:+.2f}", delta_color="inverse")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Visão geral", "⚖️ Comparação", "🔗 Correlações", "🗂️ Dados"])

# ---------- Visão geral ----------
with tab1:
    left, right = st.columns(2)

    fig = go.Figure()
    fig.add_bar(x=df.index, y=df["IPCA"], name="IPCA mensal", opacity=0.45)
    fig.add_scatter(x=df.index, y=df["IPCA_12m"], name="IPCA 12m", line=dict(width=3))
    fig.update_layout(title="Inflação (IPCA)", yaxis_title="%", legend=dict(orientation="h"))
    left.plotly_chart(fig, use_container_width=True)

    fig = go.Figure()
    fig.add_scatter(x=df.index, y=df["Selic_12m"], name="Selic 12m", line=dict(width=3))
    fig.add_scatter(x=df.index, y=df["IPCA_12m"], name="IPCA 12m")
    fig.add_scatter(x=df.index, y=df["Juro_real"], name="Juro real", fill="tozeroy", opacity=0.4)
    fig.update_layout(title="Juros: nominal x inflação x real", yaxis_title="%", legend=dict(orientation="h"))
    right.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    fig = px.area(df, y="Desemprego", title="Taxa de desocupação (%)")
    fig.update_layout(yaxis_title="%", showlegend=False)
    left.plotly_chart(fig, use_container_width=True)

    fig = px.line(df, y="Dolar", title="Dólar — média mensal (R$)")
    fig.update_layout(yaxis_title="R$", showlegend=False)
    right.plotly_chart(fig, use_container_width=True)

# ---------- Comparação ----------
with tab2:
    opcoes = ["IPCA_12m", "Selic_12m", "Juro_real", "Desemprego", "Dolar", "Dolar_var_12m"]
    sel = st.multiselect(
        "Indicadores", opcoes, default=["Desemprego", "Dolar"], format_func=LABELS.get
    )
    modo = st.radio("Escala", ["Base 100 (início do período)", "Valores originais"], horizontal=True)
    if not sel:
        st.info("Escolha ao menos um indicador.")
    else:
        if modo.startswith("Base"):
            plot = base_100(df, sel).rename(columns=LABELS)
            st.caption("Base 100 ignora valores negativos/zero de forma imprecisa — prefira indicadores positivos (Desemprego, Dólar).")
        else:
            plot = df[sel].rename(columns=LABELS)
        fig = px.line(plot)
        fig.update_layout(legend=dict(orientation="h", title=None), yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(resumo_estatistico(df, sel).rename(index=LABELS), use_container_width=True)

# ---------- Correlações ----------
with tab3:
    cols = ["IPCA", "Selic", "Desemprego", "Dolar"]
    corr = df[cols].corr().round(2)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                    title="Matriz de correlação (nível das séries)")
    st.plotly_chart(fig, use_container_width=True)
    a, b = st.columns(2)
    x = a.selectbox("Eixo X", cols, index=3)
    y = b.selectbox("Eixo Y", cols, index=2)
    fig = px.scatter(df, x=x, y=y, color=df.index.year.astype(str), title=f"{y} × {x}")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Correlação não implica causalidade — séries com tendência tendem a se correlacionar por coincidência.")

# ---------- Dados ----------
with tab4:
    show = df.rename(columns=LABELS).round(2)
    st.dataframe(show, use_container_width=True, height=420)
    st.download_button("⬇️ Baixar CSV", show.to_csv().encode("utf-8"), "painel_macro.csv", "text/csv")
