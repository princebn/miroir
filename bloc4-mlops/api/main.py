"""FastAPI app exposing /health and /recommend."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import pandas as pd
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException

from api.anchor import style_anchor_for_client
from api.model import get_model_version, load_reranker
from api.recommend import recommend as recommend_orchestrator
from api.retrieval import (
    PG_DB, PG_HOST, PG_PASSWORD, PG_PORT, PG_USER, retrieve_candidates,
)
from api.schemas import HealthResponse, RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)
_state = {"model": None}


def _load_profile(client_id: str) -> dict:
    sql = """
    SELECT client_id, morphologie, saison_colorimetrique, archetypes_style,
           budget_tranche, taille, occasions_preferees
    FROM core.client_profiles
    WHERE client_id = %s
    """
    with psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD,
    ) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (client_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"client_id not found: {client_id}")
        return dict(row)


def _features(profile: dict, candidates: list, occasion: str) -> pd.DataFrame:
    rows = []
    for c in candidates:
        rows.append({
            "client_morphologie": profile.get("morphologie") or "",
            "client_saison": profile.get("saison_colorimetrique") or "",
            "client_taille": profile.get("taille") or "",
            "client_budget": profile.get("budget_tranche") or "",
            "occasion": occasion,
            "item_article_type": c.get("article_type") or "",
            "item_base_colour": c.get("base_colour") or "",
            "item_usage": c.get("usage") or "",
            "item_season": c.get("season") or "",
            "cosine_distance": float(c.get("cosine_distance", 0.5)),
        })
    return pd.DataFrame(rows)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _state["model"] = load_reranker()
        logger.info("Reranker model loaded.")
    except Exception as e:
        logger.warning(f"Could not load reranker model: {e}")
        _state["model"] = None
    yield


app = FastAPI(title="Miroir Recommendation API", version="0.1.0", lifespan=lifespan)


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
            profile_fn=_load_profile,
            anchor_fn=style_anchor_for_client,
            retrieve_fn=retrieve_candidates,
            feature_fn=_features,
            model=_state["model"],
        )
    except KeyError as e:
        raise HTTPException(404, str(e))
    return RecommendResponse(client_id=req.client_id, occasion=req.occasion, items=items)
