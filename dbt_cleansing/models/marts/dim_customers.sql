select
    cliente_id,
    nome,
    email,
    cidade,
    data_cadastro,
    email is null as flag_email_ausente
from {{ ref('stg_clientes') }}