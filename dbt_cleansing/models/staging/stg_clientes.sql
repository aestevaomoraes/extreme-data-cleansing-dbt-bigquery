with limpo as (
    select
        safe_cast(cliente_id as int64) as cliente_id,
        initcap(lower(trim(nome))) as nome,
        lower(trim(email)) as email,
        initcap(lower(trim(cidade))) as cidade,
        coalesce(
            safe.parse_date('%d/%m/%Y', trim(data_cadastro)),
            safe.parse_date('%Y-%m-%d', trim(data_cadastro))
        ) as data_cadastro
    from {{ source('raw', 'clientes_raw') }}
)

select *
from limpo
where cliente_id is not null
qualify row_number() over (partition by cliente_id order by data_cadastro desc) = 1