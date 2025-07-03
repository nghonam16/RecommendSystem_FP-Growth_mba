SELECT
    InvoiceNo,
    CustomerID,
    trim(Description) AS item,
    Quantity
FROM {{ ref('online_retail') }}
WHERE Quantity > 0
  AND CustomerID IS NOT NULL
