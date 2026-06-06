with src as (
    select
        t_dat,
        customer_id,
        article_id,
        price,
        sales_channel_id,
        to_timestamp(ingested_at) as ingested_at,
        loaded_at
    from {{ source('signals', 'stream_transactions') }}
)
select * from src
