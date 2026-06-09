# Miroir — Bloc 4 : Solution d'IA (recommandation & MLOps)

> **Miroir industrialise le conseil en image.**
> Plateforme B2B qui outille les conseillères en image indépendantes pour personnaliser le style de leurs clientes à grande échelle.

Ce dépôt couvre le **Bloc 4 — Solutions d'IA** : conception du modèle, API de serving, CI/CD, réentraînement automatisé et monitoring en production. Cahier des charges complet : `docs/cadrage.md`.

## 1. Problème métier

Persona : **Aïcha**, conseillère en image gérant une trentaine de clientes premium en Europe et en Afrique. Chaque recommandation intègre morphologie, colorimétrie saisonnière, archétypes de style, budget, taille et occasion. Le conseil artisanal ne passe pas l'échelle : Miroir l'industrialise via un moteur de recommandation hybride, en gardant la conseillère dans la boucle (human-in-the-loop) et une gouvernance RGPD défendable (cadre B2B).

## 2. Solution ML

Recommandation en deux étages :

1. **Retrieval** — embeddings CLIP (ViT-B-32) du catalogue (44 419 articles) indexés dans Postgres/pgvector (HNSW, cosinus) ; rappel des candidats par proximité visuelle et colorimétrique.
2. **Re-ranking** — modèle **LightGBM** sur **37 features** (morphologie, colorimétrie, archétypes, budget, taille, occasion, attributs produit).

Performances sur le jeu de test :

| Métrique | Valeur |
|----------|--------|
| AUC | 0,876 |
| Average Precision | 0,80 |
| NDCG@5 | 0,42 |
| Recall@5 | 0,56 |

Les modèles sont versionnés dans le **MLflow Model Registry** (`miroir_reranker`) et servis via l'alias `@production`.

## 3. Architecture

```
Requête (cliente, occasion)
        |
        v
   API FastAPI  -->  Retrieval pgvector + CLIP  -->  Re-ranking LightGBM  -->  Top-5 tenues
        |                                                                         |
        +---------------------------  /feedback (approve / reject)  <-------------+
```

## 4. Stack technique

FastAPI · LightGBM · open_clip (ViT-B-32) · Postgres 16 + pgvector · MLflow · Docker · Airflow 2.10 · Great Expectations · Evidently 0.7 · Prometheus + Grafana · GitHub Actions.

## 5. Démarrage rapide

Prérequis : Docker, Python 3.12. L'infrastructure de données (Postgres/pgvector, MinIO, Redis) est mutualisée avec le Bloc 2.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export MLFLOW_TRACKING_URI="sqlite:///$PWD/mlflow.db"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000

curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"client_id":"<client_id>","occasion":"bureau","k":5}'
```

Endpoints : `POST /recommend`, `POST /feedback`, `GET /health`, `GET /metrics`.

## 6. CI/CD · Réentraînement · Monitoring

- **CI/CD** (`.github/workflows/bloc4-ci.yml`) : job *quality* (ruff, black, 67 tests pytest) + job *docker-build* (build multi-stage, cache).
- **Réentraînement** (`retrain/dags/miroir_reco_retrain.py`) : DAG Airflow hebdomadaire — régénération → garde-fou qualité (Great Expectations) → entraînement → **promotion conditionnelle** de l'alias `production` (rollback si l'AUC passe sous le champion − 0,005).
- **Monitoring** en trois étages : technique (latence p95 < 300 ms, débit) via Grafana ; métier (`miroir_feedback_total`) ; **drift des features** via Evidently (`monitoring/evidently/drift_report.py`).

## 7. Structure du dépôt

| Dossier | Contenu |
|---------|---------|
| `src/` | embeddings, génération synthétique, re-ranker, communs |
| `api/` | service FastAPI de serving |
| `retrain/` | scripts + DAG Airflow de réentraînement |
| `monitoring/` | drift Evidently, dashboard Grafana |
| `k8s/` | manifestes de déploiement |
| `tests/` | tests unitaires (pytest) |
| `docs/` | cahier des charges, ADR |
