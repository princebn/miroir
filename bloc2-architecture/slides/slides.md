---
marp: true
theme: default
paginate: true
header: 'Miroir — Bloc 2 : Architecture de donnees'
footer: 'github.com/princebn/miroir'
style: |
  section { font-size: 26px; }
  h1 { color: #1a1a2e; }
  h2 { color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 6px; }
  strong { color: #0f3460; }
---

# Miroir
## Bloc 2 — Architecture de donnees

Plateforme SaaS B2B de conseil en image

Prince Nehemie

---

## Le projet Miroir (fil rouge)

- **SaaS B2B** pour conseilleres en image independantes
- Persona : Aicha, 38 ans, ~30 clientes premium (Europe + Afrique)
- Pain : **60% du temps** perdu en recherche produit
- Valeur : recommandations personnalisees, **validees par la conseillere** (~10h/semaine gagnees)
- Choix B2B : RGPD defendable, human-in-the-loop, scope ML maitrise

---

## Besoins architecturaux

- Catalogue produits riche + **recherche visuelle** (embeddings CLIP)
- **Volume transactionnel** credible (collaborative filtering)
- OLTP metier + vector store + object storage + cache
- Deploiement **local reproductible** ET **cloud-ready**
- Observabilite (metriques, dashboards)

---

## Architecture globale

```
Sources              Ingestion           Stack data          Observabilite
Fashion 44k    -->   ingest_products -->  PostgreSQL 16   --> Prometheus
                     upload_images   -->  + pgvector      --> Grafana
H&M 31M tx     -->   ingest_hm       -->  MinIO (S3)
                                          Redis (cache)
```

Diagramme detaille : `docs/architecture.md`

---

## Modele de donnees — 5 schemas, 14 tables

- **core** : conseilleres, clientes, profils (morpho, palette, style)
- **catalog** : produits + `product_embeddings vector(512)` + couleurs
- **signals** : H&M brut (31M transactions) — landing zone
- **reco** : recommandations + **action conseillere** (human-in-the-loop)
- **events** : interactions (cible du stream Kafka, Bloc 3)

UUID (metier) · ENUM (integrite) · pgvector (recherche visuelle)

---

## Stack technique

| Couche         | Techno                    |
|----------------|---------------------------|
| OLTP + vecteurs| PostgreSQL 16 + pgvector  |
| Object storage | MinIO (S3-compatible)     |
| Cache          | Redis 7                   |
| Conteneurs     | Docker Compose            |
| Orchestration  | Kubernetes + Helm         |
| IaC            | Terraform (local + GCP)   |
| Observabilite  | Prometheus + Grafana      |

Stack unique alignee sur les 4 blocs.

---

## Ingestion des donnees

- **44 424 produits** (Fashion) -> `catalog.products`
- **44 441 images** -> MinIO (upload parallelise, 508 img/s)
- **31,8M transactions** H&M -> `COPY` en streaming (RAM 16 Go maitrisee)
- Approche **ELT** : on charge le brut, on transforme au Bloc 3
- Integrite verifiee : **0 transaction orpheline**

---

## Infrastructure as Code

- **Terraform local** : buckets MinIO geres en declaratif
  (import du bucket existant + creation des buckets plateforme)
- **Terraform GCP-ready** : VPC, GKE, Cloud SQL Postgres 16, GCS
  - valide (`terraform validate`), **pret a `apply`**
  - mapping direct : MinIO->GCS, Postgres->Cloud SQL, K8s->GKE

---

## Deploiement orchestre + observabilite

- **Helm chart** `miroir-stack` -> cluster Kubernetes
  - StatefulSets (Postgres, MinIO) + Deployment (Redis)
  - pods **Running**, PVC **Bound**, probes readiness/liveness
- docker-compose (dev rapide) vs K8s (orchestre, reproductible)
- **Prometheus + Grafana** : exporters Postgres/Redis, targets **UP**

---

## Decisions d'architecture (ADR)

1. **B2B SaaS** (vs B2C) — RGPD + human-in-the-loop
2. **ELT** (vs ETL) — landing brute, transformation en aval
3. **pgvector** — une seule base metier + vecteurs
4. **Compose + K8s** — dev rapide + deploiement orchestre
5. **Donnees reelles + synthetiques** — volume credible + coherence metier

Tracees dans `docs/adr/`

---

## En synthese

- Infrastructure **complete, reproductible, documentee**
- Donnees reelles a l'echelle (31,8M transactions)
- IaC local + cloud-ready, deploiement K8s effectif, monitoring actif
- Code : **github.com/princebn/miroir**
- Demo : video (infra en action)

**Merci** — questions ?
