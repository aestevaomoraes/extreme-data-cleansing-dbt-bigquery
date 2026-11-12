{{
    config(
        partition_by={
            'field': 'cliente_id',
            'data_type': 'int64',
            'range': {'start': 0, 'end': 1100, 'interval': 100}
        },
        cluster_by=['status', 'data_compra']
    )
}}

select
    transacao_id,
    cliente_id,
    produto,
    valor_brl,
    simbolo_original,
    data_compra,
    status,
    flag_valor_negativo,
    flag_anomalia,
    receita_valida
from {{ ref('int_transacoes_auditadas') }}