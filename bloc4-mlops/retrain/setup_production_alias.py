# One-shot: pose alias production sur la plus ancienne version, si aucun alias defini.
from __future__ import annotations

from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient

DB_PATH = Path(__file__).resolve().parent.parent / "mlflow.db"
TRACKING_URI = "sqlite:///" + str(DB_PATH)
MODEL_NAME = "miroir_reranker"
ALIAS = "production"


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    rm = client.get_registered_model(MODEL_NAME)
    if ALIAS in rm.aliases:
        print(f"alias {ALIAS} deja en place : v{rm.aliases[ALIAS]}")
        return
    versions = [mv for mv in client.search_model_versions() if mv.name == MODEL_NAME]
    if not versions:
        print("aucune version registree, rien a faire")
        return
    oldest = min(versions, key=lambda mv: int(mv.version))
    client.set_registered_model_alias(MODEL_NAME, ALIAS, oldest.version)
    print(f"alias {ALIAS} pose sur v{oldest.version}")


if __name__ == "__main__":
    main()
