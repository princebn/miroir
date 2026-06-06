#!/usr/bin/env python3
"""Scaffold du projet dbt Miroir (Bloc 3)."""
import os
BASE = os.path.expanduser("~/Documents/miroir/bloc3-pipelines/dbt/miroir")
FILES = {
"dbt_project.yml": """name: 'miroir'
version: '1.0.0'
profile: 'miroir'
model-paths: ["models"]
target-path: "target"
clean-targets: ["target", "dbt_packages"]
models:
  miroir:
    staging:
      +materialized: view
    marts:
      +materialized: table
""",
"profiles.yml": """miroir:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: miroir
      password: miroir_local_pwd
      dbname: miroir
      schema: analytics
      threads: 4
""",
"models/sources.yml": """version: 2
sources:
  - name: signals
    schema: signals
    tables:
      - name: stream_transactions
""",
"models/staging/stg_stream_transactions.sql": """with src as (
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
""",
"models/staging/_staging.yml": """version: 2
models:
  - name: stg_stream_transactions
    description: "Flux H&M nettoye et type."
    columns:
      - name: customer_id
        tests: [not_null]
      - name: article_id
        tests: [not_null]
      - name: sales_channel_id
        tests:
          - not_null
          - accepted_values:
              values: [1, 2]
""",
"models/marts/mart_channel_daily.sql": """select
    t_dat,
    sales_channel_id,
    count(*)                    as n_transactions,
    count(distinct customer_id) as distinct_customers,
    count(distinct article_id)  as distinct_articles
from {{ ref('stg_stream_transactions') }}
group by 1, 2
""",
"models/marts/_marts.yml": """version: 2
models:
  - name: mart_channel_daily
    description: "Volume quotidien par canal de vente."
    columns:
      - name: n_transactions
        tests: [not_null]
""",
}
for rel, content in FILES.items():
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print("ecrit:", rel)
print("OK ->", BASE)
