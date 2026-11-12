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

# Câmbio diário (taxa para BRL) de USD e EUR durante 2025
con.execute("""
    CREATE TABLE cambio_limpo AS
    SELECT
        d.data,
        m.moeda,
        round(m.base + m.amp * sin(dayofyear(d.data) / 58.0)
              + (random() - 0.5) * 0.1, 4) AS taxa_para_brl
    FROM (
        SELECT CAST(unnest(range(DATE '2025-01-01', DATE '2026-01-01', INTERVAL 1 DAY)) AS DATE) AS data
    ) d
    CROSS JOIN (VALUES ('USD', 5.2, 0.4), ('EUR', 5.8, 0.4)) m(moeda, base, amp)
""")

# Base limpa de transações, agora com moeda
con.execute(f"""
    CREATE TABLE transacoes_limpas AS
    WITH base AS (
        SELECT
            i AS transacao_id,
            1 + CAST(floor(random() * {N_CLIENTES}) AS INTEGER) AS cliente_id,
            ['Notebook', 'Mouse', 'Teclado', 'Monitor', 'Headset'][1 + CAST(floor(random() * 5) AS INTEGER)] AS produto,
            CASE WHEN random() < 0.70 THEN 'BRL'
                 WHEN random() < 0.67 THEN 'USD'
                 ELSE 'EUR' END AS moeda,
            round(50 + random() * 4950, 2) AS valor_brl,
            DATE '2025-01-01' + CAST(floor(random() * 365) AS INTEGER) AS data_compra,
            random() AS u_status
        FROM range(1, {N_TRANSACOES + 1}) t(i)
    )
    SELECT
        b.transacao_id, b.cliente_id, b.produto, b.moeda,
        CASE WHEN b.moeda = 'BRL' THEN b.valor_brl
             ELSE round(b.valor_brl / c.taxa_para_brl, 2) END AS valor,
        b.data_compra,
        CASE WHEN b.u_status < 0.80 THEN 'pago'
             WHEN b.u_status < 0.92 THEN 'cancelado'
             ELSE 'estornado' END AS status
    FROM base b
    LEFT JOIN cambio_limpo c ON c.data = b.data_compra AND c.moeda = b.moeda
""")

# Histórico: cada cliente nasce com uma cidade; ~25% mudam de cidade depois
con.execute("""
    CREATE TABLE clientes_historico_limpo AS
    SELECT cliente_id, cidade, data_cadastro AS data_inicio FROM clientes_limpos
    UNION ALL
    SELECT cliente_id, nova_cidade AS cidade,
           data_cadastro + CAST(floor(100 + random() * 500) AS INTEGER) AS data_inicio
    FROM (
        SELECT *, ['São Paulo', 'Cuiabá', 'Recife', 'Curitiba', 'Manaus'][1 + CAST(floor(random() * 5) AS INTEGER)] AS nova_cidade
        FROM clientes_limpos
        WHERE random() < 0.25
    )
    WHERE nova_cidade <> cidade
""")

print("Clientes:", con.execute("SELECT count(*) FROM clientes_limpos").fetchone()[0])
print("Transações:", con.execute("SELECT count(*) FROM transacoes_limpas").fetchone()[0])
print("Histórico:", con.execute("SELECT count(*) FROM clientes_historico_limpo").fetchone()[0])

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

# Passo intermediário: fixa os sorteios por linha numa tabela.
# Assim cada linha "decide" uma vez só o seu formato.
con.execute("""
    CREATE TABLE transacoes_pre AS
    SELECT *,
           CASE WHEN random() < 0.01 THEN -valor ELSE valor END AS valor_neg,
           random() AS r1,
           random() AS r2
    FROM (
        SELECT * FROM transacoes_limpas
        UNION ALL
        SELECT * FROM transacoes_limpas WHERE random() < 0.02  -- 2% duplicados
    )
""")

con.execute("""
    CREATE TABLE transacoes_sujas AS
    SELECT
        transacao_id,
        cliente_id,
        produto,
        CASE WHEN tem_simbolo AND r2 < 0.03 THEN NULL
             WHEN r2 < 0.10 THEN lower(moeda)
             ELSE moeda END AS moeda,
        valor_txt AS valor,
        CASE WHEN random() < 0.50 THEN strftime(data_compra, '%d/%m/%Y')
             ELSE strftime(data_compra, '%Y-%m-%d') END AS data_compra,
        CASE WHEN random() < 0.10 THEN upper(status)
             WHEN random() < 0.05 THEN ' ' || status || ' '
             ELSE status END AS status
    FROM (
        SELECT *,
            CASE
                WHEN moeda = 'BRL' AND r1 < 0.45 THEN 'R$ ' || replace(printf('%.2f', valor_neg), '.', ',')
                WHEN moeda = 'BRL' AND r1 < 0.70 THEN replace(printf('%.2f', valor_neg), '.', ',')
                WHEN moeda = 'USD' AND r1 < 0.60 THEN '$' || printf('%.2f', valor_neg)
                WHEN moeda = 'EUR' AND r1 < 0.70 THEN '€ ' || replace(printf('%.2f', valor_neg), '.', ',')
                ELSE printf('%.2f', valor_neg)
            END AS valor_txt,
            (moeda = 'BRL' AND r1 < 0.45)
              OR (moeda = 'USD' AND r1 < 0.60)
              OR (moeda = 'EUR' AND r1 < 0.70) AS tem_simbolo
        FROM transacoes_pre
    )
""")

con.execute("""
    CREATE TABLE clientes_historico_sujo AS
    SELECT
        cliente_id,
        CASE WHEN random() < 0.20 THEN lower(cidade) ELSE cidade END AS cidade,
        CASE WHEN random() < 0.50 THEN strftime(data_inicio, '%d/%m/%Y')
             ELSE strftime(data_inicio, '%Y-%m-%d') END AS data_inicio
    FROM clientes_historico_limpo
""")

# Exporta os CSVs para data/raw/ (o câmbio é uma tabela de referência, já limpa)
OUT_DIR.mkdir(parents=True, exist_ok=True)
for nome, tabela in [
    ("clientes", "clientes_sujos"),
    ("transacoes", "transacoes_sujas"),
    ("clientes_historico", "clientes_historico_sujo"),
    ("cambio", "cambio_limpo"),
]:
    caminho = OUT_DIR / f"{nome}.csv"
    con.execute(f"COPY {tabela} TO '{caminho}' (HEADER, DELIMITER ',')")
    print("Gravado:", caminho)