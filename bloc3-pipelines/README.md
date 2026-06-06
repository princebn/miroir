# Miroir — Bloc 3 : Pipeline de données temps réel

Pipeline ELT temps réel qui **rejoue les vraies transactions H&M** (jeu public,
31,8 M de lignes) comme un flux continu, les charge, les transforme, les contrôle
en qualité et orchestre le tout.

> Les prix H&M sont des **unités normalisées du dataset**, jamais des euros.

## Architecture

```
transactions_train.csv
        │  (producteur, rejeu en flux)
        ▼
   Apache Kafka  ──────────  Kafka UI (localhost:8080)
   topic miroir.transactions
        │  (consommateur, batch)
        ▼
   PostgreSQL  signals.stream_transactions   (landing)
        │  (dbt : ELT)
        ▼
   analytics.stg_stream_transactions  (vue, nettoyée + typée)
   analytics.mart_channel_daily       (table, volume/jour/canal)
        │
        ├─ dbt tests        (not_null, accepted_values…)
        └─ Great Expectations (6 expectations sur le flux chargé)

   Orchestration : Apache Airflow  (DAG miroir_pipeline)
   produce → consume → dbt_build → quality
```

## Composants

| Dossier | Rôle | Techno |
|---|---|---|
| `docker/` | broker de flux + UI | Kafka (KRaft) + Kafka UI |
| `python/produce_transactions.py` | rejeu H&M → Kafka | confluent-kafka |
| `python/consume_to_postgres.py` | Kafka → Postgres (landing) | confluent-kafka + psycopg2 |
| `dbt/miroir/` | transformations + tests | dbt-postgres 1.10 |
| `python/quality_check.py` | contrôle qualité | Great Expectations 1.18 |
| `dags/miroir_pipeline.py` | orchestration | Airflow 2.10 |

## Exécution

Pré-requis : la stack data du Bloc 2 (Postgres) tourne.

```bash
# 1. Kafka
cd docker && docker compose -f docker-compose.kafka.yml up -d && cd ..

# 2. venv data
source ../.venv/bin/activate

# 3. flux : produire puis charger
python python/produce_transactions.py --rate 500 --limit 2000
python python/consume_to_postgres.py

# 4. transformer + tester
export DBT_PROFILES_DIR=$PWD/dbt/miroir
(cd dbt/miroir && dbt build)

# 5. contrôle qualité
python python/quality_check.py

# 6. tout orchestrer (venv Airflow séparé)
source ../.venv-airflow/bin/activate
export AIRFLOW_HOME=$PWD/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$PWD/dags
airflow dags test miroir_pipeline 2026-06-06
```

## Contrôle qualité

- **dbt tests** : `not_null` sur les clés, `accepted_values` (canal ∈ {1,2}).
- **Great Expectations** : non-nullité, domaine du canal, bornes de prix, volume.
- Le DAG échoue si la qualité échoue (code de sortie propagé) → garde-fou.

## Note

Les identifiants Postgres dans les scripts/`profiles.yml` sont des **identifiants
de dev locaux** (base jetable en conteneur). En production ils seraient
externalisés (variables d'environnement / secret manager).
