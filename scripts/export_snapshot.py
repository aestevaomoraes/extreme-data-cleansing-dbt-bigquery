"""Exporta um snapshot dos marts do BigQuery para CSV.
O dashboard le esses arquivos e roda sem BigQuery, sem chave e sem expirar."""
from pathlib import Path
from google.cloud import bigquery

PROJECT = "projeto-sql-492802"
OUT = Path("data/snapshot")
OUT.mkdir(parents=True, exist_ok=True)

client = bigquery.Client(project=PROJECT)

CONSULTAS = {
    "fct_transactions": f"select * from `{PROJECT}.dbt_cleansing_marts.fct_transactions` order by transacao_id",
    "dim_customers": f"select * from `{PROJECT}.dbt_cleansing_marts.dim_customers` order by cliente_id",
    "resumo_qualidade": f"""
        select 'transacoes_brutas' as metrica, count(*) as valor
          from `{PROJECT}.dbt_cleansing_raw.transacoes_raw`
        union all select 'transacoes_tratadas', count(*)
          from `{PROJECT}.dbt_cleansing_staging.stg_transacoes`
        union all select 'clientes_brutos', count(*)
          from `{PROJECT}.dbt_cleansing_raw.clientes_raw`
        union all select 'clientes_tratados', count(*)
          from `{PROJECT}.dbt_cleansing_staging.stg_clientes`
    """,
}

for nome, sql in CONSULTAS.items():
    df = client.query(sql).to_dataframe()
    df.to_csv(OUT / f"{nome}.csv", index=False)
    print(f"{nome}: {df.shape[0]} linhas, {df.shape[1]} colunas")
