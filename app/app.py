from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

SNAP = Path(__file__).resolve().parent.parent / "data" / "snapshot"
LABELS = {"valor_brl": "Receita (BRL)", "moeda": "Moeda", "produto": "Produto", "mes": "Mês"}

st.set_page_config(page_title="Saneamento Extremo", layout="wide")


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data
def carregar():
    fct = pd.read_csv(SNAP / "fct_transactions.csv", parse_dates=["data_compra"])
    dim = pd.read_csv(SNAP / "dim_customers.csv")
    qual = pd.read_csv(SNAP / "resumo_qualidade.csv")
    return fct, dim, qual


fct, dim, qual = carregar()

# ---------- Filtros ----------
st.sidebar.header("Filtros")
todas_moedas = sorted(fct["moeda"].dropna().unique())
moedas = st.sidebar.multiselect("Moeda", todas_moedas, default=todas_moedas)
d_min = fct["data_compra"].min().date()
d_max = fct["data_compra"].max().date()
periodo = st.sidebar.date_input(
    "Período", (d_min, d_max), min_value=d_min, max_value=d_max
)
if len(periodo) != 2:
    st.stop()

mascara = fct["moeda"].isin(moedas) & fct["data_compra"].between(
    pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
)
filtrado = fct[mascara]
validas = filtrado[filtrado["receita_valida"]]

# ---------- Cabeçalho e KPIs ----------
st.title("Saneamento Extremo & Data Quality")
st.caption("Fonte: marts do dbt (snapshot do BigQuery)")

if validas.empty:
    st.warning("Nenhuma transação válida para os filtros escolhidos.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Receita válida (BRL)", brl(validas["valor_brl"].sum()))
c2.metric("Transações válidas", f"{len(validas):,}".replace(",", "."))
c3.metric("Ticket médio (BRL)", brl(validas["valor_brl"].mean()))

# ---------- Gráficos de negócio ----------
col_a, col_b = st.columns(2)

por_moeda = validas.groupby("moeda", as_index=False)["valor_brl"].sum()
col_a.plotly_chart(
    px.bar(por_moeda, x="moeda", y="valor_brl", title="Receita por moeda (BRL)", labels=LABELS),
    width="stretch",
)

por_produto = (
    validas.groupby("produto", as_index=False)["valor_brl"]
    .sum()
    .sort_values("valor_brl")
)
col_b.plotly_chart(
    px.bar(
        por_produto,
        x="valor_brl",
        y="produto",
        orientation="h",
        title="Receita por produto (BRL)", labels=LABELS,
    ),
    width="stretch",
)

mensal = (
    validas.assign(mes=validas["data_compra"].dt.to_period("M").dt.to_timestamp())
    .groupby("mes", as_index=False)["valor_brl"]
    .sum()
)
st.plotly_chart(
    px.line(mensal, x="mes", y="valor_brl", markers=True, title="Receita mensal (BRL)", labels=LABELS),
    width="stretch",
)
