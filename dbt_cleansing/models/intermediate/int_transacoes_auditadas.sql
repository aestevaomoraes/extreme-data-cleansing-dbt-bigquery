select
    t.transacao_id,
    t.cliente_id,
    c.cidade,
    t.produto,
    t.valor_brl,
    t.simbolo_original,
    t.data_compra,
    t.status,

    t.valor_brl < 0 as flag_valor_negativo,
    t.data_compra < c.data_cadastro as flag_compra_antes_cadastro,
    c.email is null as flag_cliente_sem_email,

    (t.valor_brl < 0
        or t.data_compra < c.data_cadastro) as flag_anomalia,

    (t.status = 'pago' and t.valor_brl >= 0) as receita_valida
from {{ ref('stg_transacoes') }} as t
left join {{ ref('stg_clientes') }} as c
    on t.cliente_id = c.cliente_id