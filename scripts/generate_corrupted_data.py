import duckdb
from pathlib import Path

SEED = 0.42          # semente fixa: mesmo resultado em toda execução
N_CLIENTES = 1_000
N_TRANSACOES = 10_000
OUT_DIR = Path("data/raw")

con = duckdb.connect()  # banco em memória, sem arquivo no disco
con.execute(f"SELECT setseed({SEED})")

# Base limpa de clientes: é o "gabarito" que vamos usar nos testes
con.execute(f"""
    CREATE TABLE clientes_limpos AS
    SELECT
        i AS cliente_id,
        'Cliente ' || i AS nome,
        'cliente' || i || '@exemplo.com' AS email,
        ['São Paulo', 'Cuiabá', 'Recife', 'Curitiba', 'Manaus'][1 + CAST(floor(random() * 5) AS INTEGER)] AS cidade,
        DATE '2022-01-01' + CAST(floor(random() * 900) AS INTEGER) AS data_cadastro
    FROM range(1, {N_CLIENTES + 1}) t(i)
""")

# Base limpa de transações
con.execute(f"""
    CREATE TABLE transacoes_limpas AS
    SELECT
        i AS transacao_id,
        1 + CAST(floor(random() * {N_CLIENTES}) AS INTEGER) AS cliente_id,
        ['Notebook', 'Mouse', 'Teclado', 'Monitor', 'Headset'][1 + CAST(floor(random() * 5) AS INTEGER)] AS produto,
        round(50 + random() * 4950, 2) AS valor,
        DATE '2025-01-01' + CAST(floor(random() * 365) AS INTEGER) AS data_compra,
        ['pago', 'cancelado', 'estornado'][1 + CAST(floor(random() * 3) AS INTEGER)] AS status
    FROM range(1, {N_TRANSACOES + 1}) t(i)
""")

print("Clientes:", con.execute("SELECT count(*) FROM clientes_limpos").fetchone()[0])
print("Transações:", con.execute("SELECT count(*) FROM transacoes_limpas").fetchone()[0])

# ---------- PARTE B: sujar os dados ----------

con.execute("""
    CREATE TABLE clientes_sujos AS
    SELECT
        cliente_id,
        CASE WHEN random() < 0.15 THEN upper(nome)
             WHEN random() < 0.30 THEN '  ' || nome || ' '
             ELSE nome END AS nome,
        CASE WHEN random() < 0.03 THEN NULL ELSE email END AS email,
        CASE WHEN random() < 0.20 THEN lower(cidade) ELSE cidade END AS cidade,
        CASE WHEN random() < 0.50 THEN strftime(data_cadastro, '%d/%m/%Y')
             ELSE strftime(data_cadastro, '%Y-%m-%d') END AS data_cadastro
    FROM (
        SELECT * FROM clientes_limpos
        UNION ALL
        SELECT * FROM clientes_limpos WHERE random() < 0.05  -- 5% duplicados
    )
""")

con.execute("""
    CREATE TABLE transacoes_sujas AS
    SELECT
        transacao_id,
        cliente_id,
        produto,
        CASE WHEN random() < 0.33 THEN 'R$ ' || replace(printf('%.2f', valor_neg), '.', ',')
             WHEN random() < 0.50 THEN '$' || printf('%.2f', valor_neg)
             ELSE printf('%.2f', valor_neg) END AS valor,
        CASE WHEN random() < 0.50 THEN strftime(data_compra, '%d/%m/%Y')
             ELSE strftime(data_compra, '%Y-%m-%d') END AS data_compra,
        CASE WHEN random() < 0.10 THEN upper(status)
             WHEN random() < 0.05 THEN ' ' || status || ' '
             ELSE status END AS status
    FROM (
        SELECT *, CASE WHEN random() < 0.01 THEN -valor ELSE valor END AS valor_neg
        FROM (
            SELECT * FROM transacoes_limpas
            UNION ALL
            SELECT * FROM transacoes_limpas WHERE random() < 0.02  -- 2% duplicados
        )
    )
""")

# Exporta os CSVs sujos para data/raw/
OUT_DIR.mkdir(parents=True, exist_ok=True)
for nome, tabela in [("clientes", "clientes_sujos"), ("transacoes", "transacoes_sujas")]:
    caminho = OUT_DIR / f"{nome}.csv"
    con.execute(f"COPY {tabela} TO '{caminho}' (HEADER, DELIMITER ',')")
    print("Gravado:", caminho)