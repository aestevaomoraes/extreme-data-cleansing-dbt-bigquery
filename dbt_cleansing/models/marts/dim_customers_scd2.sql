with versoes as (
    select
        cliente_id,
        cidade,
        data_inicio as valid_from,
        lead(data_inicio) over (partition by cliente_id order by data_inicio) as proxima_inicio
    from {{ ref('stg_clientes_historico') }}
)

select
    to_hex(md5(concat(cast(v.cliente_id as string), '|', cast(v.valid_from as string)))) as cliente_sk,
    v.cliente_id,
    c.nome,
    c.email,
    v.cidade,
    v.valid_from,
    coalesce(date_sub(v.proxima_inicio, interval 1 day), date '9999-12-31') as valid_to,
    v.proxima_inicio is null as is_current
from versoes as v
left join {{ ref('stg_clientes') }} as c
    on v.cliente_id = c.cliente_id