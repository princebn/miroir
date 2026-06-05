# Miroir — Bloc 2 : Architecture de données

Infrastructure de données complète pour **Miroir**, plateforme SaaS B2B de conseil
en image. Ce bloc couvre l'architecture, le modèle de données, l'IaC, le déploiement
orchestré et l'observabilité.

## Architecture

Voir [docs/architecture.md](docs/architecture.md) et le modèle de données
[docs/data-model.md](docs/data-model.md). Décisions justifiées dans [docs/adr/](docs/adr/).

## Stack technique

| Couche          | Techno                        | Rôle                              |
|-----------------|-------------------------------|-----------------------------------|
| OLTP + vecteurs | PostgreSQL 16 + pgvector      | Données métier + embeddings CLIP  |
| Object storage  | MinIO (S3-compatible)         | Images produits, artefacts        |
| Cache           | Redis 7                       | Cache applicatif                  |
| Conteneurs      | Docker Compose                | Boucle dev locale                 |
| Orchestration   | Kubernetes (Helm chart)       | Déploiement reproductible         |
| IaC             | Terraform (local + GCP-ready) | Provisioning déclaratif           |
| Observabilité   | Prometheus + Grafana          | Métriques + dashboards            |

## Structure

    bloc2-architecture/
    ├── db/                 # DDL du modèle (schema.sql, indexes)
    ├── docker/             # docker-compose stack data + init SQL
    ├── scripts/            # ingestion (produits, images, H&M)
    ├── terraform/
    │   ├── local/          # buckets MinIO (provider minio)
    │   └── gcp/            # VPC, GKE, Cloud SQL, GCS (GCP-ready)
    ├── k8s/
    │   ├── helm/           # chart miroir-stack
    │   └── manifests/      # manifests rendus
    ├── monitoring/         # Prometheus + Grafana + exporters
    └── docs/               # architecture, data-model, ADR

## Démarrage rapide

    # 1. Stack data
    cd docker && docker compose up -d
    # 2. Schéma + index
    psql "$DATABASE_URL" -f ../db/schema.sql
    psql "$DATABASE_URL" -f ../db/indexes_signals.sql
    # 3. Ingestion (venv actif)
    cd ../scripts && python ingest_products.py && python upload_images.py && python ingest_hm.py
    # 4. IaC buckets
    cd ../terraform/local && terraform init && terraform apply
    # 5. Déploiement K8s
    helm install miroir-stack ../../k8s/helm/miroir-stack -n miroir --create-namespace
    # 6. Monitoring
    cd ../../monitoring && docker compose -f docker-compose.monitoring.yml up -d

## Accès aux services

| Service    | URL                   | Auth                       |
|------------|-----------------------|----------------------------|
| PostgreSQL | localhost:5432        | miroir / (voir .env)       |
| MinIO API  | http://localhost:9000 | miroir_admin / (voir .env) |
| MinIO UI   | http://localhost:9001 | idem                       |
| Redis      | localhost:6379        | (voir .env)                |
| Prometheus | http://localhost:9090 | -                          |
| Grafana    | http://localhost:3000 | admin / (voir compose)     |

## Volumétrie

- 44 424 produits + 44 441 images (MinIO)
- 105 542 articles, 1 371 980 clients, 31 788 324 transactions H&M (signal collaborative)
