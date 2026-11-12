with base as (
    select
        safe_cast(transacao_id as int64) as transacao_id,
        safe_cast(cliente_id as int64) as cliente_id,
        initcap(lower(trim(produto))) as produto,
        nullif(upper(trim(moeda)), '') as moeda_informada,
        trim(valor) as valor_txt,
        coalesce(
            safe.parse_date('%d/%m/%Y', trim(data_compra)),
            safe.parse_date('%Y-%m-%d', trim(data_compra))
        ) as data_compra,
        lower(trim(status)) as status
    from {{ source('raw', 'transacoes_raw') }}
),

limpo as (
    select
        transacao_id,
        cliente_id,
        produto,
        coalesce(
            moeda_informada,
            case
                when starts_with(valor_txt, 'R$') then 'BRL'
                when starts_with(valor_txt, '€') then 'EUR'
                when starts_with(valor_txt, '$') then 'USD'
                else 'BRL'
            end
        ) as moeda,
        moeda_informada is null as flag_moeda_inferida,
        {{ safe_currency('valor_txt') }} as valor_original,
        case
            when starts_with(valor_txt, 'R$') then 'R$'
            when starts_with(valor_txt, '€') then '€'
            when starts_with(valor_txt, '$') then '$'
            else 'sem simbolo'
        end as simbolo_original,
        data_compra,
        status
    from base
)

select *
from limpo
where transacao_id is not null
qualify row_number() over (partition by transacao_id order by data_compra desc) = 1