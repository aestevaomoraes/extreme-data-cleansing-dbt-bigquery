select
    safe.parse_date('%Y-%m-%d', trim(data)) as data,
    upper(trim(moeda)) as moeda,
    safe_cast(taxa_para_brl as numeric) as taxa_para_brl
from {{ source('raw', 'cambio_raw') }}
where safe_cast(taxa_para_brl as numeric) is not null
qualify row_number() over (partition by data, moeda order by taxa_para_brl) = 1