"""
src/reranker/features.py

Feature engineering pour le re-ranker.

Convertit profil cliente + occasion active + item du catalogue en features
numériques pour LightGBM.

Conventions :
- Catégoriels avec petit vocabulaire (morph., saison, occasion, archétypes) →
  one-hot ou multi-hot
- Ordinaux (budget, taille) → entier
- Catégoriels avec gros vocabulaire (article_type ~140, base_colour ~46,
  sub_category ~50) → passés en string, LightGBM les traite nativement
  via le paramètre `categorical_feature`

Aucune colonne des scores intermédiaires (color_score, etc.) ne doit
apparaître dans X : ce serait de la fuite (le label est dérivé d'eux).
"""

from __future__ import annotations

import pandas as pd

# ============================================================================
# Vocabulaires (doivent rester cohérents avec src/synth/generate_profiles.py)
# ============================================================================

MORPHOLOGIES = ["sablier", "rectangle", "triangle", "triangle_inverse", "ovale"]

SAISONS = [
    "printemps_clair",
    "printemps_chaud",
    "printemps_lumineux",
    "ete_doux",
    "ete_froid",
    "ete_lumineux",
    "automne_chaud",
    "automne_profond",
    "automne_doux",
    "hiver_froid",
    "hiver_profond",
    "hiver_lumineux",
]

ARCHETYPES = ["classique", "naturel", "romantique", "dramatique", "creatif", "elegant_chic"]
BUDGETS = ["bas", "milieu_bas", "milieu_haut", "premium"]
OCCASIONS = ["bureau", "cocktail", "vacances", "sport", "soiree", "casual"]
TAILLES = ["XS", "S", "M", "L", "XL"]

ITEM_CATEGORICAL_COLS = [
    "item_master_category",
    "item_sub_category",
    "item_article_type",
    "item_base_colour",
    "item_season",
    "item_usage",
]

_BUDGET_ORD = {b: i for i, b in enumerate(BUDGETS)}
_TAILLE_ORD = {t: i for i, t in enumerate(TAILLES)}


# ============================================================================
# Encodages unitaires (utilisés en tests, et conservés comme spec lisible)
# ============================================================================


def encode_profile_features(profile_row: pd.Series) -> dict[str, float]:
    """One-hot / multi-hot / ordinal d'un profil cliente unique."""
    feats: dict[str, float] = {}
    for m in MORPHOLOGIES:
        feats[f"morph_{m}"] = 1.0 if profile_row["morphologie"] == m else 0.0
    for s in SAISONS:
        feats[f"saison_{s}"] = 1.0 if profile_row["saison_colorimetrique"] == s else 0.0
    arch = set(profile_row["archetypes"])
    for a in ARCHETYPES:
        feats[f"arch_{a}"] = 1.0 if a in arch else 0.0
    feats["budget_ord"] = float(_BUDGET_ORD[profile_row["budget_tranche"]])
    feats["taille_ord"] = float(_TAILLE_ORD[profile_row["taille"]])
    return feats


def encode_occasion(occasion: str) -> dict[str, float]:
    """One-hot de l'occasion active de l'interaction."""
    return {f"occ_{o}": 1.0 if o == occasion else 0.0 for o in OCCASIONS}


# ============================================================================
# Build vectorisé (production : 45 000 interactions en <1 s)
# ============================================================================


def build_features(
    interactions: pd.DataFrame,
    profiles: pd.DataFrame,
    catalog: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Construit X (features), y (labels), groups (client_id).

    Args:
        interactions : DataFrame avec colonnes [client_id, item_id, occasion, label, ...]
        profiles     : DataFrame avec colonnes [client_id, morphologie, saison_colorimetrique,
                         archetypes, budget_tranche, taille, occasions, ...]
        catalog      : DataFrame avec colonnes [item_id, master_category, sub_category,
                         article_type, base_colour, season, usage]

    Returns:
        X      : features (interactions × n_features)
        y      : labels (interactions,)
        groups : client_id par row (pour le split)
    """
    needed_prof = [
        "client_id",
        "morphologie",
        "saison_colorimetrique",
        "archetypes",
        "budget_tranche",
        "taille",
    ]
    prof_slim = profiles[needed_prof]

    cat_slim = catalog[
        [
            "item_id",
            "master_category",
            "sub_category",
            "article_type",
            "base_colour",
            "season",
            "usage",
        ]
    ].rename(
        columns={
            "master_category": "item_master_category",
            "sub_category": "item_sub_category",
            "article_type": "item_article_type",
            "base_colour": "item_base_colour",
            "season": "item_season",
            "usage": "item_usage",
        }
    )

    # On ne prend QUE les colonnes nécessaires des interactions, jamais les scores.
    inter_slim = interactions[["client_id", "item_id", "occasion", "label"]]

    df = inter_slim.merge(prof_slim, on="client_id", how="left")
    df = df.merge(cat_slim, on="item_id", how="left")

    out = pd.DataFrame(index=df.index)

    for m in MORPHOLOGIES:
        out[f"morph_{m}"] = (df["morphologie"] == m).astype(float)
    for s in SAISONS:
        out[f"saison_{s}"] = (df["saison_colorimetrique"] == s).astype(float)
    for a in ARCHETYPES:
        out[f"arch_{a}"] = df["archetypes"].apply(lambda lst, a=a: 1.0 if a in lst else 0.0)
    out["budget_ord"] = df["budget_tranche"].map(_BUDGET_ORD).astype(float)
    out["taille_ord"] = df["taille"].map(_TAILLE_ORD).astype(float)

    for o in OCCASIONS:
        out[f"occ_{o}"] = (df["occasion"] == o).astype(float)

    for col in ITEM_CATEGORICAL_COLS:
        out[col] = df[col].astype("string")

    y = df["label"]
    groups = df["client_id"]
    return out, y, groups
