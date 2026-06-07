{{ config(materialized='table', tags=['reference']) }}
select
  coalesce(nullif(btrim(a.index_name), ''), 'Inconnu')          as segment,
  coalesce(nullif(btrim(a.product_group_name), ''), 'Inconnu')  as categorie,
  count(*) as n_transactions
from {{ source('signals','hm_transactions') }} t
join {{ source('signals','hm_articles') }} a using (article_id)
group by 1, 2
