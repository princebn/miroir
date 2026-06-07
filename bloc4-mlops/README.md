# Bloc 4 — Solutions d'IA (Miroir Reco)

Voir `docs/cadrage.md` pour le cahier des charges complet.

## Structure
- `src/` — code source (embeddings CLIP, génération synthétique, re-ranker, communs)
- `notebooks/` — exploration et analyses
- `tests/` — tests unitaires (pytest)
- `data/synthetic/` — données synthétiques générées
- `models/` — artefacts entraînés (ignorés par git, suivis via MLflow)
- `api/` — service FastAPI de serving
- `k8s/` — manifestes Kubernetes (cible cloud)
- `monitoring/` — rapports Evidently, configs Prometheus
- `retrain/` — DAG Airflow de réentraînement
- `docs/` — cadrage, ADR

## Statut
En cours d'implémentation. Phase actuelle : initialisation du squelette.
