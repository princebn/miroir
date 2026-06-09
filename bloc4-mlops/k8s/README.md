# k8s/

Manifestes de déploiement de l'API de recommandation sur Kubernetes (cible cluster).

- `deployment.yaml` — Deployment `miroir-api` : 2 répliques (serving sans état), sondes `readiness`/`liveness` sur `/health`, variables OpenMP pour la cohabitation LightGBM/CLIP (voir ADR-0007), requests/limits CPU et mémoire.
- `service.yaml` — Service `ClusterIP` exposant l'API sur le port 80 → 8000.

Déploiement : `kubectl apply -f k8s/`.

> La démonstration tourne en local via Docker. Ces manifestes décrivent la cible de déploiement en cluster ; en production, le `MLFLOW_TRACKING_URI` pointerait vers un serveur MLflow externe (registry partagé entre les répliques) plutôt qu'un SQLite embarqué.
