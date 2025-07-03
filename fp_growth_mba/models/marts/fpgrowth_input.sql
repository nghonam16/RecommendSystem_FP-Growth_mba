
select
    InvoiceNo as transaction_id,
    group_concat(item, ',') as items
from {{ ref('stg_online_retail') }}
group by InvoiceNo