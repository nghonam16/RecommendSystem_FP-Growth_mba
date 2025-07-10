{{ config(materialized='view') }}

SELECT
    CustomerID AS user_id,
    StockCode AS item_id
FROM {{ ref('stg_online_retail') }}
WHERE CustomerID IS NOT NULL AND StockCode IS NOT NULL
GROUP BY CustomerID, StockCode
