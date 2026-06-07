{{ config(materialized='table', tags=['reference']) }}
select
  coalesce(nullif(btrim(a.index_name), ''), 'Inconnu') as segment,
  count(*)                      as n_transactions,
  count(distinct t.customer_id) as distinct_customers,
  count(distinct t.article_id)  as distinct_articles
from {{ source('signals','hm_transactions') }} t
join {{ source('signals','hm_articles') }} a using (article_id)
group by 1
