"""Load the trained reranker from MLflow Model Registry."""

from __future__ import annotations

import os
from typing import Optional

import mlflow
import mlflow.lightgbm

DEFAULT_TRACKING_URI = "sqlite:///mlflow.db"
DEFAULT_MODEL_URI = "models:/miroir_reranker/1"


def load_reranker():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)
    model_uri = os.environ.get("MIROIR_RERANKER_URI", DEFAULT_MODEL_URI)
    mlflow.set_tracking_uri(tracking_uri)
    return mlflow.lightgbm.load_model(model_uri)


def get_model_version() -> Optional[str]:
    model_uri = os.environ.get("MIROIR_RERANKER_URI", DEFAULT_MODEL_URI)
    if "/" in model_uri:
        return model_uri.rsplit("/", 1)[-1]
    return None
