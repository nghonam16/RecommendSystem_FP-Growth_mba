WITH ranked AS (
    SELECT
        StockCode AS product_id,
        Description,
        ROW_NUMBER() OVER (PARTITION BY StockCode ORDER BY Description) as row_num
    FROM {{ ref('stg_online_retail') }}
    WHERE StockCode IS NOT NULL AND Description IS NOT NULL
)

SELECT
    product_id,
    ROUND(ABS(RANDOM()) % 5000 / 100.0 + 1, 2) AS price,
    CASE
        WHEN instr(Description, 'LED') > 0 THEN 'Lighting'
        WHEN instr(Description, 'TOY') > 0 THEN 'Toys'
        WHEN instr(Description, 'CARD') > 0 THEN 'Stationery'
        ELSE 'General'
    END AS category
FROM ranked
WHERE row_num = 1
