select
    t_dat,
    sales_channel_id,
    count(*)                    as n_transactions,
    count(distinct customer_id) as distinct_customers,
    count(distinct article_id)  as distinct_articles
from {{ ref('stg_stream_transactions') }}
group by 1, 2
