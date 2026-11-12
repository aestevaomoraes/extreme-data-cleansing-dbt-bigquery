select
    safe_cast(cliente_id as int64) as cliente_id,
    initcap(lower(trim(cidade))) as cidade,
    coalesce(
        safe.parse_date('%d/%m/%Y', trim(data_inicio)),
        safe.parse_date('%Y-%m-%d', trim(data_inicio))
    ) as data_inicio
from {{ source('raw', 'clientes_historico_raw') }}
where safe_cast(cliente_id as int64) is not null
qualify row_number() over (partition by cliente_id, data_inicio order by cidade) = 1