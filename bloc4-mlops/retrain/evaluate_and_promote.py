# Compare la version la plus recente (challenger) au champion (alias production)
# sur test.parquet ; promeut si auc_new >= auc_old - tolerance, sinon rollback.
from __future__ import annotations

from pathlib import Path

import mlflow
import mlflow.lightgbm
import pandas as pd
from mlflow.tracking import MlflowClient
from sklearn.metrics import roc_auc_score

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "mlflow.db"
TRACKING_URI = "sqlite:///" + str(DB_PATH)
TEST_PATH = BASE / "data" / "synthetic" / "test.parquet"
TRAIN_PATH = BASE / "data" / "synthetic" / "train.parquet"
MODEL_NAME = "miroir_reranker"
ALIAS = "production"
TOLERANCE = 0.005
# A garder aligne avec src/reranker/features.py:ITEM_CATEGORICAL_COLS
ITEM_CATEGORICAL_COLS = [
    "item_master_category",
    "item_sub_category",
    "item_article_type",
    "item_base_colour",
    "item_season",
    "item_usage",
]


def prepare_test():
    test = pd.read_parquet(TEST_PATH)
    train = pd.read_parquet(TRAIN_PATH)
    y = test.pop("__label").astype(int).to_numpy()
    test.pop("__client_id")
    for col in ITEM_CATEGORICAL_COLS:
        cats = pd.Index(train[col].dropna().unique()).sort_values()
        test[col] = pd.Categorical(test[col].astype(str), categories=cats)
    return test, y


def auc_of(version, X, y):
    m = mlflow.lightgbm.load_model(f"models:/{MODEL_NAME}/{version}")
    if hasattr(m, "predict_proba"):
        p = m.predict_proba(X)[:, 1]
    else:
        p = m.predict(X)
    return roc_auc_score(y, p)


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    versions = [mv for mv in client.search_model_versions() if mv.name == MODEL_NAME]
    if not versions:
        print("Aucune version registree.")
        return
    versions.sort(key=lambda mv: int(mv.version), reverse=True)
    challenger = versions[0]
    print(f"Challenger : v{challenger.version}")
    rm = client.get_registered_model(MODEL_NAME)
    if ALIAS not in rm.aliases:
        client.set_registered_model_alias(MODEL_NAME, ALIAS, challenger.version)
        print(f"Cas initial : alias {ALIAS} pose sur v{challenger.version}")
        return
    champion_version = rm.aliases[ALIAS]
    print(f"Champion (alias {ALIAS}) : v{champion_version}")
    if str(challenger.version) == str(champion_version):
        print("Le challenger EST deja le champion. Rien a promouvoir.")
        return
    X, y = prepare_test()
    auc_new = auc_of(challenger.version, X, y)
    auc_old = auc_of(champion_version, X, y)
    print(f"AUC challenger v{challenger.version} : {auc_new:.4f}")
    print(f"AUC champion   v{champion_version} : {auc_old:.4f}")
    print(f"Tolerance : {TOLERANCE}")
    if auc_new >= auc_old - TOLERANCE:
        client.set_registered_model_alias(MODEL_NAME, ALIAS, challenger.version)
        print(f"DECISION : PROMU. alias {ALIAS} -> v{challenger.version}")
    else:
        print(f"DECISION : ROLLBACK. v{champion_version} reste en production.")


if __name__ == "__main__":
    main()
