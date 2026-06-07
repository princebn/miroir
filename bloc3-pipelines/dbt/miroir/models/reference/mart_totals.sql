{{ config(materialized='table', tags=['reference']) }}
select
  count(*)                    as n_transactions,
  count(distinct customer_id) as distinct_customers,
  count(distinct article_id)  as distinct_articles
from {{ source('signals','hm_transactions') }}
