# Load the trained reranker from MLflow Model Registry via alias production (fallback v1).
from __future__ import annotations

import os
from typing import Optional

import mlflow
import mlflow.lightgbm
from mlflow.tracking import MlflowClient

DEFAULT_TRACKING_URI = "sqlite:///mlflow.db"
DEFAULT_MODEL_URI = "models:/miroir_reranker@production"
MODEL_NAME = "miroir_reranker"
ALIAS = "production"


def load_reranker():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)
    mlflow.set_tracking_uri(tracking_uri)
    model_uri = os.environ.get("MIROIR_RERANKER_URI", DEFAULT_MODEL_URI)
    try:
        return mlflow.lightgbm.load_model(model_uri)
    except Exception:
        return mlflow.lightgbm.load_model("models:/miroir_reranker/1")


def get_model_version() -> Optional[str]:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)
    try:
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient()
        mv = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
        return mv.version
    except Exception:
        model_uri = os.environ.get("MIROIR_RERANKER_URI", DEFAULT_MODEL_URI)
        if "@" in model_uri:
            return None
        if "/" in model_uri:
            return model_uri.rsplit("/", 1)[-1]
        return None
