from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

SNAP = Path(__file__).resolve().parent.parent.parent / "data" / "snapshot"

st.set_page_config(page_title="Qualidade", layout="wide")


@st.cache_data
def carregar():
    fct = pd.read_csv(SNAP / "fct_transactions.csv", parse_dates=["data_compra"])
    dim = pd.read_csv(SNAP / "dim_customers.csv")
    qual = pd.read_csv(SNAP / "resumo_qualidade.csv")
    return fct, dim, qual


fct, dim, qual = carregar()
resumo = dict(zip(qual["metrica"], qual["valor"]))


def contar(df, col):
    return int(df[col].fillna(False).astype(bool).sum())


st.title("Qualidade e Auditoria dos Dados")
st.caption("O que o pipeline encontrou de sujo e como tratou")

dup_transacoes = int(resumo["transacoes_brutas"] - resumo["transacoes_tratadas"])
dup_clientes = int(resumo["clientes_brutos"] - resumo["clientes_tratados"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Transações duplicadas removidas", dup_transacoes)
c2.metric("Clientes duplicados removidos", dup_clientes)
c3.metric("Clientes sem e-mail", contar(dim, "flag_email_ausente"))
c4.metric("Moedas inferidas pelo símbolo", contar(fct, "flag_moeda_inferida"))

col_a, col_b = st.columns(2)

ocorrencias = pd.DataFrame(
    {
        "problema": [
            "Moeda inferida",
            "Valor negativo",
            "Anomalia",
        ],
        "transacoes": [
            contar(fct, "flag_moeda_inferida"),
            contar(fct, "flag_valor_negativo"),
            contar(fct, "flag_anomalia"),
        ],
    }
)
col_a.plotly_chart(
    px.bar(
        ocorrencias,
        x="transacoes",
        y="problema",
        orientation="h",
        title="Ocorrências por tipo de problema", labels={"problema": "Problema", "transacoes": "Transações"},
    ),
    width="stretch",
)

status = fct["status"].value_counts().reset_index()
status.columns = ["status", "transacoes"]
col_b.plotly_chart(
    px.bar(status, x="status", y="transacoes", title="Transações por status", labels={"status": "Status", "transacoes": "Transações"}),
    width="stretch",
)

st.subheader("Transações marcadas como anomalia")
anomalias = fct[fct["flag_anomalia"].fillna(False).astype(bool)]
st.dataframe(
    anomalias[
        ["transacao_id", "produto", "moeda", "valor_original", "valor_brl", "status", "data_compra"]
    ].head(100).assign(data_compra=lambda d: d["data_compra"].dt.date),
    hide_index=True,
    width="stretch",
)
