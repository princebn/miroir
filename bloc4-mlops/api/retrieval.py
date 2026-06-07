"""Candidate retrieval via pgvector cosine similarity + hard filters."""
from __future__ import annotations

import os
from typing import Iterable, List

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor

OCCASION_TO_USAGES = {
    "bureau": ["Formal", "Smart Casual"],
    "cocktail": ["Party", "Formal"],
    "vacances": ["Casual", "Sports"],
    "sport": ["Sports"],
    "soiree": ["Party", "Formal"],
    "casual": ["Casual", "Smart Casual"],
}

PG_HOST = os.environ.get("MIROIR_PG_HOST", "localhost")
PG_PORT = int(os.environ.get("MIROIR_PG_PORT", "5432"))
PG_DB = os.environ.get("MIROIR_PG_DB", "miroir")
PG_USER = os.environ.get("MIROIR_PG_USER", "miroir")
PG_PASSWORD = os.environ.get("MIROIR_PG_PASSWORD", "miroir_local_pwd")
CATALOG_TABLE = os.environ.get("MIROIR_CATALOG_TABLE", "catalog.item_embeddings")


def _pg():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD,
    )


def _vector_literal(v: np.ndarray) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def retrieve_candidates(
    anchor: np.ndarray,
    occasion: str,
    n_candidates: int = 200,
    gender_allowed: Iterable[str] = ("Women", "Unisex"),
) -> List[dict]:
    usages = OCCASION_TO_USAGES.get(occasion, []) or [
        "Casual", "Formal", "Smart Casual", "Party", "Sports",
    ]
    anchor_str = _vector_literal(anchor)
    sql = f"""
    SELECT
      item_id, master_category, sub_category, article_type,
      base_colour, season, usage, gender,
      image_path AS image_url,
      product_display_name,
      (embedding <=> %s::vector) AS cosine_distance
    FROM {CATALOG_TABLE}
    WHERE gender = ANY(%s) AND usage = ANY(%s) AND embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """
    with _pg() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (anchor_str, list(gender_allowed), usages, anchor_str, n_candidates))
        return [dict(row) for row in cur.fetchall()]
