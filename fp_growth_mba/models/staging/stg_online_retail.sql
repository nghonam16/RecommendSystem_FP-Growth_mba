{{ config(materialized='view') }}

SELECT
    *
FROM {{ ref('online_retail') }}
