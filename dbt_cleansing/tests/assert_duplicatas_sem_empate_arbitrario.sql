-- Falha se, depois dos criterios de negocio (data, valor nao negativo,
-- moeda informada), ainda houver versoes divergentes empatadas:
-- nesse caso so o hash decidiria, o que seria arbitrario.
with ranqueado as (
    select
        *,
        dense_rank() over (
            partition by transacao_id
            order by
                data_compra desc,
                coalesce(valor_original < 0, true),
                flag_moeda_inferida,
                (simbolo_original = 'sem simbolo')
        ) as posicao
    from {{ ref('stg_transacoes_limpo') }}
)

select transacao_id
from ranqueado as r
where posicao = 1
group by transacao_id
having count(distinct to_json_string(r)) > 1
