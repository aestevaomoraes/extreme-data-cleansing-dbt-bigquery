with limpo as (
    select
        safe_cast(transacao_id as int64) as transacao_id,
        safe_cast(cliente_id as int64) as cliente_id,
        initcap(lower(trim(produto))) as produto,
        {{ safe_currency('trim(valor)') }} as valor_brl,
        case
            when starts_with(trim(valor), 'R$') then 'R$'
            when starts_with(trim(valor), '$') then '$'
            when starts_with(trim(valor), '€') then '€'
            else 'sem simbolo'
        end as simbolo_original,
        coalesce(
            safe.parse_date('%d/%m/%Y', trim(data_compra)),
            safe.parse_date('%Y-%m-%d', trim(data_compra))
        ) as data_compra,
        lower(trim(status)) as status
    from {{ source('raw', 'transacoes_raw') }}
)

select *
from limpo
where transacao_id is not null
qualify row_number() over (partition by transacao_id order by data_compra desc) = 1