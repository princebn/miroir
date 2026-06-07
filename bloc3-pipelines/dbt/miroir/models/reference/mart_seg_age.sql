{{ config(materialized='table', tags=['reference']) }}
select
  coalesce(nullif(btrim(a.index_name), ''), 'Inconnu') as segment,
  case
    when c.age is null then 'Inconnu'
    when c.age < 25 then '16-24'
    when c.age < 35 then '25-34'
    when c.age < 45 then '35-44'
    when c.age < 55 then '45-54'
    else '55+'
  end as tranche_age,
  count(*) as n_transactions
from {{ source('signals','hm_transactions') }} t
join {{ source('signals','hm_articles') }} a using (article_id)
join {{ source('signals','hm_customers') }} c using (customer_id)
group by 1, 2
