"""
src/synth/generate_interactions.py

Génère N interactions synthétiques (cliente × article × occasion → label)
à partir :
- des 1 500 profils synthétiques (data/synthetic/profiles.parquet)
- des 44 419 articles du catalogue (catalog.item_embeddings dans Postgres)

Règle d'étiquetage : score combiné couleur + occasion + archétype, seuillé
à 0,70, avec 5 % de label flip pour simuler le bruit humain.

Spec : data/synthetic/spec.md (section Interactions)
Sortie : data/synthetic/interactions.parquet

Usage:
    python -m src.synth.generate_interactions
    python src/synth/generate_interactions.py --per-client 30 --seed 42
"""
from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.db import get_conn
from src.synth.compatibility import (
    APPROVAL_THRESHOLD,
    LABEL_FLIP_PROB,
    combined_score,
)


PROFILES_PATH = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "profiles.parquet"
INTERACTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "interactions.parquet"


def load_catalog_metadata() -> pd.DataFrame:
    """Charge la métadonnée des articles depuis Postgres (sans le vecteur)."""
    conn = get_conn(register_pgvector=False)
    sql = """
        SELECT
            item_id, gender, master_category, sub_category,
            article_type, base_colour, season, usage, product_display_name
        FROM catalog.item_embeddings
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


def filter_for_women(catalog: pd.DataFrame) -> pd.DataFrame:
    """Filtre dur : la persona Aïcha sert des clientes — donc Women + Unisex."""
    keep = catalog["gender"].isin(["Women", "Unisex"])
    out = catalog[keep].reset_index(drop=True)
    print(f"Catalogue Women+Unisex : {len(out):,} articles sur {len(catalog):,}")
    return out


def _new_uuid(rng: np.random.Generator) -> str:
    return str(uuid.UUID(bytes=rng.bytes(16)))


def generate_interactions(
    profiles: pd.DataFrame,
    catalog: pd.DataFrame,
    per_client: int = 30,
    seed: int = 42,
) -> pd.DataFrame:
    """Pour chaque cliente, échantillonne `per_client` articles aléatoires et étiquette.

    Retourne un DataFrame avec colonnes :
      interaction_id, client_id, item_id, occasion, label,
      color_score, occasion_score, archetype_score, combined_score
    """
    rng = np.random.default_rng(seed)
    catalog_n = len(catalog)
    rows = []

    for _, profile in profiles.iterrows():
        # 1. Échantillonne `per_client` articles aléatoires depuis le catalogue Women/Unisex
        idx = rng.choice(catalog_n, size=per_client, replace=False)
        sampled = catalog.iloc[idx]

        # 2. Choisit une occasion par interaction (parmi celles de la cliente)
        client_occasions = list(profile["occasions"])

        for _, item in sampled.iterrows():
            occasion = str(rng.choice(client_occasions))
            cs, os_, as_, comb = combined_score(
                color=item["base_colour"],
                usage=item["usage"],
                article_type=item["article_type"],
                saison=profile["saison_colorimetrique"],
                occasion=occasion,
                archetypes=list(profile["archetypes"]),
            )

            # 3. Étiquette = seuil + bruit
            base_label = 1 if comb >= APPROVAL_THRESHOLD else 0
            if rng.random() < LABEL_FLIP_PROB:
                base_label = 1 - base_label

            rows.append({
                "interaction_id": _new_uuid(rng),
                "client_id": profile["client_id"],
                "item_id": item["item_id"],
                "occasion": occasion,
                "label": base_label,
                "color_score": round(cs, 3),
                "occasion_score": round(os_, 3),
                "archetype_score": round(as_, 3),
                "combined_score": round(comb, 3),
            })

    return pd.DataFrame(rows)


def main(per_client: int = 30, seed: int = 42) -> None:
    if not PROFILES_PATH.exists():
        raise SystemExit(
            f"profils introuvables : {PROFILES_PATH}\n"
            "Lance d'abord : python -m src.synth.generate_profiles"
        )

    profiles = pd.read_parquet(PROFILES_PATH)
    print(f"Profils chargés : {len(profiles):,}")

    catalog = load_catalog_metadata()
    print(f"Catalogue total : {len(catalog):,}")

    catalog = filter_for_women(catalog)
    if len(catalog) < per_client:
        raise SystemExit(f"Catalogue trop petit ({len(catalog)}) pour échantillonner {per_client}")

    print(f"Génération de {len(profiles)} × {per_client} = {len(profiles) * per_client:,} interactions…")
    df = generate_interactions(profiles, catalog, per_client=per_client, seed=seed)

    INTERACTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(INTERACTIONS_PATH, index=False)

    print(f"\nOK — {len(df):,} interactions écrites dans {INTERACTIONS_PATH}")
    print()
    print("Statistiques de sortie :")
    label_rate = df["label"].mean()
    print(f"  Taux d'approbation : {label_rate:.1%}")
    print(f"  Score combiné — moyenne : {df['combined_score'].mean():.3f}")
    print(f"  Score combiné — médiane : {df['combined_score'].median():.3f}")

    per_client_stats = df.groupby("client_id")["label"].agg(["sum", "count"])
    per_client_stats["rate"] = per_client_stats["sum"] / per_client_stats["count"]
    print(f"  Clientes avec 0 approuvé : {(per_client_stats['sum'] == 0).sum()}")
    print(f"  Clientes avec 100 % approuvé : {(per_client_stats['rate'] == 1.0).sum()}")
    print(f"  Article-id distincts utilisés : {df['item_id'].nunique():,}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate synthetic client × item interactions")
    p.add_argument("--per-client", type=int, default=30, help="Interactions par cliente")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    main(per_client=args.per_client, seed=args.seed)
