

select
    cast(CustomerID as text) as user_id,
    item as item_id
from {{ ref('stg_online_retail') }}