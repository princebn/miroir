# models/

Les artefacts de modèle ne sont **pas** versionnés en fichiers ici : ils sont gérés par le **MLflow Model Registry** (backend SQLite `mlflow.db`, artefacts sous `mlruns/`, tous deux ignorés par git).

- Modèle enregistré : `miroir_reranker`
- Version servie : alias `@production`, déplacé automatiquement par le DAG de réentraînement (voir ADR-0004 et ADR-0005)
- Chargement applicatif : `mlflow.lightgbm.load_model("models:/miroir_reranker@production")` dans `api/model.py`

Inspecter versions et métriques :

    mlflow ui --backend-store-uri sqlite:///mlflow.db
