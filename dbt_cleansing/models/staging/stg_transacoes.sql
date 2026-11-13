select *
from {{ ref('stg_transacoes_limpo') }} as l
qualify row_number() over (
    partition by transacao_id
        order by
        data_compra desc,
        coalesce(valor_original < 0, true),
        flag_moeda_inferida,
        (simbolo_original = 'sem simbolo'),
        farm_fingerprint(to_json_string(l))
) = 1