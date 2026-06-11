import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import lightgbm  # noqa: F401

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

from api.anchor import style_anchor_for_client
from api.demo_routes import router as demo_router
from api.model import get_model_version, load_reranker
from api.recommend import recommend as recommend_orchestrator
from api.retrieval import retrieve_candidates
from api.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    RecommendRequest,
    RecommendResponse,
)
from src.reranker.features import ITEM_CATEGORICAL_COLS
import psycopg2
from api.retrieval import PG_DB, PG_HOST, PG_PASSWORD, PG_PORT, PG_USER
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("miroir.api")

_BASE = Path(__file__).resolve().parent.parent
_PROFILES_PATH = Path(
    os.environ.get("MIROIR_PROFILES_PATH", str(_BASE / "data" / "synthetic" / "profiles.parquet"))
)
_TRAIN_PATH = Path(
    os.environ.get("MIROIR_TRAIN_PATH", str(_BASE / "data" / "synthetic" / "train.parquet"))
)

_state = {"model": None, "profiles": None, "train_categories": {}}


class _PredictorWrapper:
    def __init__(self, m):
        self._m = m

    def predict(self, X):
        return self._m.predict(X, num_threads=1)


def _load_profiles_once():
    if _state["profiles"] is None:
        _state["profiles"] = pd.read_parquet(_PROFILES_PATH)
        logger.info("profiles loaded: " + str(len(_state["profiles"])))
    return _state["profiles"]


def _load_train_categories_once():
    if not _state["train_categories"]:
        train = pd.read_parquet(_TRAIN_PATH)
        for col in ITEM_CATEGORICAL_COLS:
            _state["train_categories"][col] = pd.Index(train[col].dropna().unique()).sort_values()
        logger.info("train categories loaded: " + str(len(_state["train_categories"])))
    return _state["train_categories"]


def _load_profile(client_id):
    df = _load_profiles_once()
    matches = df[df["client_id"] == client_id]
    if matches.empty:
        raise KeyError("client_id not found: " + str(client_id))
    row = matches.iloc[0]
    return {
        "client_id": str(row["client_id"]),
        "morphologie": str(row["morphologie"]),
        "saison_colorimetrique": str(row["saison_colorimetrique"]),
        "archetypes": list(row["archetypes"]),
        "budget_tranche": str(row["budget_tranche"]),
        "taille": str(row["taille"]),
    }


def _features(profile, candidates, occasion):
    from src.reranker.features import build_features as _build

    profile_df = pd.DataFrame(
        [
            {
                "client_id": profile["client_id"],
                "morphologie": profile["morphologie"],
                "saison_colorimetrique": profile["saison_colorimetrique"],
                "archetypes": profile["archetypes"],
                "budget_tranche": profile["budget_tranche"],
                "taille": profile["taille"],
            }
        ]
    )
    catalog_df = pd.DataFrame(
        [
            {
                "item_id": c["item_id"],
                "master_category": c.get("master_category"),
                "sub_category": c.get("sub_category"),
                "article_type": c.get("article_type"),
                "base_colour": c.get("base_colour"),
                "season": c.get("season"),
                "usage": c.get("usage"),
            }
            for c in candidates
        ]
    )
    interactions_df = pd.DataFrame(
        [
            {
                "client_id": profile["client_id"],
                "item_id": c["item_id"],
                "occasion": occasion,
                "label": 0,
            }
            for c in candidates
        ]
    )
    X, _, _ = _build(interactions_df, profile_df, catalog_df)
    cats = _load_train_categories_once()
    for col in ITEM_CATEGORICAL_COLS:
        X[col] = pd.Categorical(X[col].astype(str), categories=cats[col])
    return X


@asynccontextmanager
async def lifespan(app):
    logger.info("=== STARTUP ===")
    try:
        _state["model"] = _PredictorWrapper(load_reranker())
        logger.info("reranker loaded")
    except Exception as e:
        logger.warning("reranker load failed: " + str(e))
        _state["model"] = None
    try:
        _load_profiles_once()
        _load_train_categories_once()
    except Exception as e:
        logger.warning("data preload failed: " + str(e))
    try:
        logger.info("CLIP pre-warm...")
        _ = style_anchor_for_client("bureau", "automne_doux", ["classique"])
        logger.info("CLIP pre-warmed")
    except Exception as e:
        logger.warning("CLIP pre-warm failed: " + str(e))
    logger.info("=== READY ===")
    yield


app = FastAPI(title="Miroir Recommendation API", version="0.1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
FEEDBACK_COUNTER = Counter("miroir_feedback_total", "Feedback events by action", ["action"])


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok" if _state["model"] is not None else "degraded",
        model_version=get_model_version() if _state["model"] is not None else None,
        n_catalog_items=None,
    )


@app.post("/recommend", response_model=RecommendResponse)
def recommend_endpoint(req: RecommendRequest):
    if _state["model"] is None:
        raise HTTPException(503, "Model not loaded")
    try:
        items = recommend_orchestrator(
            client_id=req.client_id,
            occasion=req.occasion,
            k=req.k,
            exclude_ids=req.exclude_ids,
            max_per_type=2,
            profile_fn=_load_profile,
            anchor_fn=style_anchor_for_client,
            retrieve_fn=retrieve_candidates,
            feature_fn=_features,
            model=_state["model"],
        )
    except KeyError as e:
        raise HTTPException(404, str(e))
    return RecommendResponse(client_id=req.client_id, occasion=req.occasion, items=items)


@app.post("/feedback", response_model=FeedbackResponse)
def feedback_endpoint(req: FeedbackRequest):
    with (
        psycopg2.connect(
            host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
        ) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(
            "INSERT INTO signals.feedback (client_id, item_id, occasion, action, score, model_version) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING feedback_id",
            (req.client_id, req.item_id, req.occasion, req.action, req.score, req.model_version),
        )
        fid = cur.fetchone()[0]
        conn.commit()
    FEEDBACK_COUNTER.labels(action=req.action).inc()
    return FeedbackResponse(feedback_id=fid, status="recorded")


app.include_router(demo_router)
