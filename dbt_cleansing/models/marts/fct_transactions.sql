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
    f.transacao_id,
    d.cliente_sk,
    f.cliente_id,
    d.cidade as cidade_na_compra,
    f.produto,
    f.moeda,
    f.valor_original,
    f.taxa_cambio,
    f.valor_brl,
    f.simbolo_original,
    f.flag_moeda_inferida,
    f.data_compra,
    f.status,
    f.flag_valor_negativo,
    f.flag_anomalia,
    f.receita_valida
from {{ ref('int_transacoes_auditadas') }} as f
left join {{ ref('dim_customers_scd2') }} as d
    on f.cliente_id = d.cliente_id
    and f.data_compra between d.valid_from and d.valid_to