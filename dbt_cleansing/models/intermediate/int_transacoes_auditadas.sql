select
    t.transacao_id,
    t.cliente_id,
    c.cidade,
    t.produto,
    t.moeda,
    t.valor_original,
    t.simbolo_original,
    t.flag_moeda_inferida,
    case when t.moeda = 'BRL' then 1 else fx.taxa_para_brl end as taxa_cambio,
    round(
        t.valor_original * case when t.moeda = 'BRL' then 1 else fx.taxa_para_brl end,
        2
    ) as valor_brl,
    t.data_compra,
    t.status,

    t.valor_original < 0 as flag_valor_negativo,
    t.data_compra < c.data_cadastro as flag_compra_antes_cadastro,
    c.email is null as flag_cliente_sem_email,
    (t.moeda != 'BRL' and fx.taxa_para_brl is null) as flag_sem_cambio,

    (t.valor_original < 0
        or t.data_compra < c.data_cadastro
        or (t.moeda != 'BRL' and fx.taxa_para_brl is null)) as flag_anomalia,

    (t.status = 'pago'
        and t.valor_original >= 0
        and (t.moeda = 'BRL' or fx.taxa_para_brl is not null)) as receita_valida
from {{ ref('stg_transacoes') }} as t
left join {{ ref('stg_clientes') }} as c
    on t.cliente_id = c.cliente_id
left join {{ ref('stg_cambio') }} as fx
    on fx.data = t.data_compra
    and fx.moeda = t.moeda