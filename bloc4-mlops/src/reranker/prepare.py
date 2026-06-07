"""
src/reranker/prepare.py

Construit le dataset d'entraînement du re-ranker.

Étapes :
  1. Charge profils.parquet, interactions.parquet, et la métadonnée catalogue
     depuis Postgres (table catalog.item_embeddings)
  2. Construit les features (one-hot + ordinal + catégoriels passthrough)
  3. Split par cliente (80 / 10 / 10)
  4. Écrit train.parquet, val.parquet, test.parquet dans data/synthetic/

Usage :
    python -m src.reranker.prepare
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.db import get_conn
from src.reranker.features import ITEM_CATEGORICAL_COLS, build_features
from src.reranker.split import group_split

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
PROFILES_PATH = DATA_DIR / "profiles.parquet"
INTERACTIONS_PATH = DATA_DIR / "interactions.parquet"

OUT_TRAIN = DATA_DIR / "train.parquet"
OUT_VAL = DATA_DIR / "val.parquet"
OUT_TEST = DATA_DIR / "test.parquet"


def load_catalog_metadata() -> pd.DataFrame:
    """Charge la métadonnée du catalogue depuis Postgres (sans le vecteur).

    Utilise un curseur psycopg2 + DataFrame plutôt que pd.read_sql pour éviter
    le warning d'incompatibilité SQLAlchemy.
    """
    conn = get_conn(register_pgvector=False)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT item_id, master_category, sub_category, article_type,
                       base_colour, season, usage
                FROM catalog.item_embeddings
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=cols)


def save_split(X: pd.DataFrame, y: pd.Series, groups: pd.Series, path: Path) -> None:
    """Sérialise un split en un parquet unique."""
    df = X.copy()
    df["__label"] = y.values
    df["__client_id"] = groups.values
    df.to_parquet(path, index=False)


def main() -> None:
    if not PROFILES_PATH.exists():
        raise SystemExit(f"Profils introuvables : {PROFILES_PATH}\n"
                         "Lance d'abord : python -m src.synth.generate_profiles")
    if not INTERACTIONS_PATH.exists():
        raise SystemExit(f"Interactions introuvables : {INTERACTIONS_PATH}\n"
                         "Lance d'abord : python -m src.synth.generate_interactions")

    print("Chargement profils, interactions, catalogue…")
    profiles = pd.read_parquet(PROFILES_PATH)
    interactions = pd.read_parquet(INTERACTIONS_PATH)
    catalog = load_catalog_metadata()
    print(f"  Profils     : {len(profiles):,}")
    print(f"  Interactions: {len(interactions):,}")
    print(f"  Catalogue   : {len(catalog):,}")

    print("Construction des features…")
    X, y, groups = build_features(interactions, profiles, catalog)
    print(f"  X shape  : {X.shape}")
    print(f"  Colonnes catégoriques (LightGBM native) : {ITEM_CATEGORICAL_COLS}")

    print("Split par cliente (80 / 10 / 10)…")
    (X_tr, y_tr, g_tr), (X_vl, y_vl, g_vl), (X_te, y_te, g_te) = group_split(
        X, y, groups, val_frac=0.10, test_frac=0.10, seed=42
    )
    print(f"  Train : {len(X_tr):,} interactions, {g_tr.nunique():,} clientes, "
          f"approbation {y_tr.mean():.1%}")
    print(f"  Val   : {len(X_vl):,} interactions, {g_vl.nunique():,} clientes, "
          f"approbation {y_vl.mean():.1%}")
    print(f"  Test  : {len(X_te):,} interactions, {g_te.nunique():,} clientes, "
          f"approbation {y_te.mean():.1%}")

    print("Écriture des parquets…")
    save_split(X_tr, y_tr, g_tr, OUT_TRAIN)
    save_split(X_vl, y_vl, g_vl, OUT_VAL)
    save_split(X_te, y_te, g_te, OUT_TEST)
    print(f"  → {OUT_TRAIN.name}, {OUT_VAL.name}, {OUT_TEST.name}")


if __name__ == "__main__":
    main()
