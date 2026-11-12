select
    cliente_id,
    countif(is_current) as versoes_vigentes
from {{ ref('dim_customers_scd2') }}
group by cliente_id
having countif(is_current) != 1