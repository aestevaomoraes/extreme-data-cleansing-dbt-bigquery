select
    transacao_id,
    valor_brl,
    status
from {{ ref('fct_transactions') }}
where receita_valida
  and valor_brl < 0