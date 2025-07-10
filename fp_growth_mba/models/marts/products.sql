{{ config(materialized='table') }}

SELECT DISTINCT
    StockCode AS product_id,
    ROUND(ABS(RANDOM()) % 5000 / 100.0 + 1, 2) AS price,
    CASE
        WHEN instr(Description, 'LED') > 0 THEN 'Lighting'
        WHEN instr(Description, 'TOY') > 0 THEN 'Toys'
        WHEN instr(Description, 'CARD') > 0 THEN 'Stationery'
        ELSE 'General'
    END AS category
FROM {{ ref('stg_online_retail') }}
WHERE Description IS NOT NULL AND StockCode IS NOT NULL
