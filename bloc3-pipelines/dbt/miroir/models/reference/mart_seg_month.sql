{{ config(materialized='table', tags=['reference']) }}
select
  coalesce(nullif(btrim(a.index_name), ''), 'Inconnu') as segment,
  date_trunc('month', t.t_dat)::date as mois,
  count(*) as n_transactions
from {{ source('signals','hm_transactions') }} t
join {{ source('signals','hm_articles') }} a using (article_id)
group by 1, 2
