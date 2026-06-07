"""
src/embeddings/embed_catalog.py

Calcule les embeddings CLIP du catalogue Fashion Product Images (~44k articles)
et les stocke dans `catalog.item_embeddings` (pgvector).

Modèle    : OpenAI CLIP ViT-B/32 (frozen) via open_clip_torch.
Dimension : 512, vecteur L2-normalisé (cosine = produit scalaire).

Idempotent : ne ré-embed que les articles absents de la table. Relançable
après interruption.

Usage:
    # smoke test (50 articles, ~30 s)
    python src/embeddings/embed_catalog.py --limit 50

    # full run (~10-20 min sur M4 / MPS)
    python src/embeddings/embed_catalog.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm

from src.common.db import get_conn


# ============================================================================
# Configuration
# ============================================================================

CATALOG_DIR = Path(os.environ.get(
    "MIROIR_CATALOG_DIR",
    "~/Downloads/archive fashion",
)).expanduser()

MODEL_NAME = "ViT-B-32"
PRETRAINED = "openai"
BATCH_SIZE = 64
EMBED_DIM = 512


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS catalog;

CREATE TABLE IF NOT EXISTS catalog.item_embeddings (
    item_id              text PRIMARY KEY,
    embedding            vector(512) NOT NULL,
    image_path           text,
    gender               text,
    master_category      text,
    sub_category         text,
    article_type         text,
    base_colour          text,
    season               text,
    usage                text,
    product_display_name text,
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_item_embeddings_hnsw
    ON catalog.item_embeddings USING hnsw (embedding vector_cosine_ops);
"""


INSERT_SQL = """
INSERT INTO catalog.item_embeddings (
    item_id, embedding, image_path,
    gender, master_category, sub_category, article_type,
    base_colour, season, usage, product_display_name
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (item_id) DO NOTHING
"""


# ============================================================================
# DB
# ============================================================================

def init_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()


def existing_item_ids(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT item_id FROM catalog.item_embeddings")
        return {r[0] for r in cur.fetchall()}


def insert_batch(conn, rows: list[tuple]) -> int:
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL, rows)
    conn.commit()
    return len(rows)


# ============================================================================
# CLIP
# ============================================================================

def get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_clip(device: str):
    model, _, preprocess = open_clip.create_model_and_transforms(
        MODEL_NAME, pretrained=PRETRAINED, force_quick_gelu=True
    )
    model.to(device).eval()
    return model, preprocess


def encode_images(paths: list[Path], model, preprocess, device: str) -> np.ndarray:
    images = [preprocess(Image.open(p).convert("RGB")) for p in paths]
    batch = torch.stack(images).to(device)
    with torch.no_grad():
        feats = model.encode_image(batch)
        feats = feats / feats.norm(dim=-1, keepdim=True)  # normalise pour cosine
    return feats.cpu().float().numpy()


# ============================================================================
# Catalogue
# ============================================================================

def _opt(v):
    """Convertit NaN / None pour psycopg2."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return str(v)


def load_catalog() -> pd.DataFrame:
    csv_path = CATALOG_DIR / "styles.csv"
    if not csv_path.exists():
        sys.exit(f"styles.csv introuvable : {csv_path}")

    df = pd.read_csv(csv_path, on_bad_lines="skip")
    df["item_id"] = df["id"].astype(str)
    df["image_path"] = df["id"].astype(str).apply(
        lambda i: CATALOG_DIR / "images" / f"{i}.jpg"
    )

    before = len(df)
    df = df[df["image_path"].apply(lambda p: p.exists())].reset_index(drop=True)
    print(f"styles.csv : {before} lignes  |  images présentes : {len(df)}")
    return df


# ============================================================================
# Main
# ============================================================================

def main(limit: int | None = None) -> None:
    print(f"Catalogue : {CATALOG_DIR}")
    if not CATALOG_DIR.exists():
        sys.exit(f"Dossier catalogue introuvable : {CATALOG_DIR}")

    device = get_device()
    print(f"Device    : {device}")

    print("Chargement CLIP (ViT-B/32, OpenAI)…")
    model, preprocess = load_clip(device)

    conn = get_conn()
    init_schema(conn)
    print("Schéma catalog.item_embeddings prêt.")

    done = existing_item_ids(conn)
    print(f"Déjà embeddés en base : {len(done):,}")

    df = load_catalog()
    todo = df[~df["item_id"].isin(done)].reset_index(drop=True)
    if limit:
        todo = todo.head(limit)
    print(f"À traiter : {len(todo):,}")

    if len(todo) == 0:
        print("Rien à faire. Sortie.")
        conn.close()
        return

    inserted = 0
    for i in tqdm(range(0, len(todo), BATCH_SIZE), desc="batches"):
        batch = todo.iloc[i:i + BATCH_SIZE]

        try:
            embs = encode_images(batch["image_path"].tolist(), model, preprocess, device)
        except Exception as e:
            print(f"\n⚠️  Échec batch {i}–{i+len(batch)} : {e} — skip")
            continue

        rows = []
        for k, (_, row) in enumerate(batch.iterrows()):
            rows.append((
                str(row["item_id"]),
                embs[k],
                str(row["image_path"]),
                _opt(row.get("gender")),
                _opt(row.get("masterCategory")),
                _opt(row.get("subCategory")),
                _opt(row.get("articleType")),
                _opt(row.get("baseColour")),
                _opt(row.get("season")),
                _opt(row.get("usage")),
                _opt(row.get("productDisplayName")),
            ))
        inserted += insert_batch(conn, rows)

    conn.close()
    print(f"\nTerminé. Lignes traitées : {inserted:,}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Embed catalog articles via CLIP into pgvector")
    p.add_argument("--limit", type=int, default=None, help="Limite (smoke test)")
    args = p.parse_args()
    main(limit=args.limit)
