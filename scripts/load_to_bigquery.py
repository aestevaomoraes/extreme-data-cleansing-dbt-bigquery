from pathlib import Path
from google.cloud import bigquery

PROJECT_ID = "projeto-sql-492802"
DATASET = "dbt_cleansing_raw"
DATA_DIR = Path("data/raw")

client = bigquery.Client(project=PROJECT_ID)

# Cria o dataset se ele ainda não existir
dataset_id = f"{PROJECT_ID}.{DATASET}"
client.create_dataset(dataset_id, exists_ok=True)
print("Dataset pronto:", dataset_id)

def carregar(arquivo, tabela, colunas):
    table_id = f"{dataset_id}.{tabela}"
    # Todas as colunas como STRING: a raw não converte nada
    schema = [bigquery.SchemaField(c, "STRING") for c in colunas]
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # pula o cabeçalho
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # substitui a tabela
    )
    with open(arquivo, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
    job.result()  # espera o job terminar
    linhas = client.get_table(table_id).num_rows
    print(f"Carregado: {table_id} ({linhas} linhas)")

carregar(DATA_DIR / "clientes.csv", "clientes_raw",
         ["cliente_id", "nome", "email", "cidade", "data_cadastro"])
carregar(DATA_DIR / "transacoes.csv", "transacoes_raw",
         ["transacao_id", "cliente_id", "produto", "valor", "data_compra", "status"])