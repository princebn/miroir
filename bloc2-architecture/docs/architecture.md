# Architecture Miroir — Bloc 2

## Vue d'ensemble

```mermaid
flowchart LR
  subgraph Sources["Sources de donnees"]
    F["Fashion Product Images<br/>44k produits + images"]
    H["H&M Dataset<br/>31M transactions"]
  end
  subgraph Ingestion["Ingestion (Python)"]
    I1["ingest_products.py"]
    I2["upload_images.py"]
    I3["ingest_hm.py"]
  end
  subgraph Stack["Stack data"]
    PG[("PostgreSQL 16<br/>+ pgvector")]
    MINIO[("MinIO<br/>object storage S3")]
    REDIS[("Redis<br/>cache")]
  end
  subgraph Obs["Observabilite"]
    PROM["Prometheus"]
    GRAF["Grafana"]
  end
  F --> I1 --> PG
  F --> I2 --> MINIO
  H --> I3 --> PG
  PG --> PROM
  REDIS --> PROM
  PROM --> GRAF
```

## Couches

- **Sources** : donnees reelles (Fashion, H&M) + donnees synthetiques generees (Bloc 3).
- **Ingestion** : scripts Python idempotents. `COPY` en streaming pour les gros volumes
  (31M transactions sans saturer la RAM), staging + `INSERT SELECT` pour la selection de colonnes.
- **Stack data** : PostgreSQL (OLTP + vector store via pgvector), MinIO (images/artefacts),
  Redis (cache). Schemas logiques : `core`, `catalog`, `signals`, `reco`, `events`.
- **Observabilite** : exporters Postgres/Redis scrapes par Prometheus, visualises dans Grafana.

## Local vs Cloud

- **Local** : Docker Compose (dev) + Kubernetes via Docker Desktop (orchestration, Helm chart).
- **Cloud (GCP-ready)** : modules Terraform `terraform/gcp/` (VPC, GKE, Cloud SQL Postgres 16,
  buckets GCS), valides via `terraform validate`, prets a `apply`. Mapping direct :
  MinIO vers GCS, Postgres conteneur vers Cloud SQL, K8s local vers GKE.
