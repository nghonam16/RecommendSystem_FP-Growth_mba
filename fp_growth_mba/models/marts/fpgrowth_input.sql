{{ config(materialized='view') }}

WITH base AS (
    SELECT
        InvoiceNo,
        StockCode
    FROM {{ ref('stg_online_retail') }}
    WHERE InvoiceNo IS NOT NULL AND StockCode IS NOT NULL
)

SELECT
    InvoiceNo,
    group_concat(StockCode, ',') AS products
FROM base
GROUP BY InvoiceNo
