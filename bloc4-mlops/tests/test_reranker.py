"""
tests/test_reranker.py

Tests du feature engineering et du split du re-ranker.
Vérifient : sanity des encodages, absence de leakage, reproductibilité,
pas de chevauchement de clientes entre splits.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.reranker.features import (
    ARCHETYPES, BUDGETS, ITEM_CATEGORICAL_COLS, MORPHOLOGIES,
    OCCASIONS, SAISONS, TAILLES,
    build_features, encode_occasion, encode_profile_features,
)
from src.reranker.split import group_split


def _profile_row(**overrides) -> pd.Series:
    base = {
        "morphologie": "sablier",
        "saison_colorimetrique": "printemps_clair",
        "archetypes": ["naturel"],
        "budget_tranche": "milieu_bas",
        "taille": "M",
    }
    base.update(overrides)
    return pd.Series(base)


def _mini_profiles(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame({
        "client_id": [f"c{i:03d}" for i in range(n)],
        "consultante_id": ["k1"] * n,
        "morphologie": (["sablier", "rectangle", "triangle", "ovale"] * (n // 4 + 1))[:n],
        "saison_colorimetrique": (
            ["printemps_clair", "hiver_froid", "automne_chaud", "ete_doux"] * (n // 4 + 1)
        )[:n],
        "archetypes": (
            [["naturel"], ["classique", "elegant_chic"], ["romantique"], ["dramatique"]]
            * (n // 4 + 1)
        )[:n],
        "budget_tranche": (["milieu_bas", "milieu_haut", "premium", "bas"] * (n // 4 + 1))[:n],
        "occasions": [["bureau"]] * n,
        "taille": (["M", "L", "S", "XS"] * (n // 4 + 1))[:n],
    })


def _mini_catalog(n: int = 10) -> pd.DataFrame:
    return pd.DataFrame({
        "item_id": [f"it{i:03d}" for i in range(n)],
        "master_category": ["Apparel"] * n,
        "sub_category": ["Topwear"] * (n // 2) + ["Bottomwear"] * (n - n // 2),
        "article_type": ["Tshirts"] * (n // 2) + ["Jeans"] * (n - n // 2),
        "base_colour": (["Blue", "Red", "Black"] * (n // 3 + 1))[:n],
        "season": ["Summer"] * n,
        "usage": ["Casual"] * n,
    })


def _mini_interactions(profiles: pd.DataFrame, catalog: pd.DataFrame,
                       n_per_client: int = 5) -> pd.DataFrame:
    rows = []
    for _, prof in profiles.iterrows():
        for j in range(n_per_client):
            rows.append({
                "interaction_id": f"i_{prof['client_id']}_{j}",
                "client_id": prof["client_id"],
                "item_id": catalog.iloc[j]["item_id"],
                "occasion": prof["occasions"][0],
                "label": j % 2,
            })
    return pd.DataFrame(rows)


# ============================================================================
# Encodages unitaires
# ============================================================================

def test_profile_morphology_onehot():
    feats = encode_profile_features(_profile_row(morphologie="sablier"))
    assert feats["morph_sablier"] == 1.0
    assert feats["morph_rectangle"] == 0.0
    assert sum(feats[f"morph_{m}"] for m in MORPHOLOGIES) == 1.0


def test_profile_saison_onehot_covers_12():
    for s in SAISONS:
        feats = encode_profile_features(_profile_row(saison_colorimetrique=s))
        assert feats[f"saison_{s}"] == 1.0
        assert sum(feats[f"saison_{x}"] for x in SAISONS) == 1.0


def test_profile_archetypes_multi_hot():
    feats = encode_profile_features(_profile_row(archetypes=["naturel", "creatif"]))
    assert feats["arch_naturel"] == 1.0
    assert feats["arch_creatif"] == 1.0
    assert feats["arch_classique"] == 0.0


def test_profile_budget_ordinal_monotonic():
    for i, b in enumerate(BUDGETS):
        feats = encode_profile_features(_profile_row(budget_tranche=b))
        assert feats["budget_ord"] == float(i)


def test_profile_taille_ordinal_monotonic():
    for i, t in enumerate(TAILLES):
        feats = encode_profile_features(_profile_row(taille=t))
        assert feats["taille_ord"] == float(i)


def test_occasion_onehot_sums_to_one():
    feats = encode_occasion("bureau")
    assert feats["occ_bureau"] == 1.0
    assert sum(feats.values()) == 1.0


# ============================================================================
# build_features — vectorisé
# ============================================================================

def test_build_features_shape_matches_interactions():
    profiles = _mini_profiles()
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog, n_per_client=5)

    X, y, groups = build_features(interactions, profiles, catalog)

    assert len(X) == len(interactions) == 20
    assert len(y) == 20
    assert len(groups) == 20


def test_build_features_contains_expected_columns():
    profiles = _mini_profiles()
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog)

    X, _, _ = build_features(interactions, profiles, catalog)

    # one-hot profil
    assert "morph_sablier" in X.columns
    assert "saison_printemps_clair" in X.columns
    assert "arch_naturel" in X.columns
    # ordinal
    assert "budget_ord" in X.columns
    assert "taille_ord" in X.columns
    # occasion
    assert "occ_bureau" in X.columns
    # item catégoriel passthrough
    for col in ITEM_CATEGORICAL_COLS:
        assert col in X.columns


def test_build_features_excludes_label_and_client_id():
    profiles = _mini_profiles()
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog)

    X, _, _ = build_features(interactions, profiles, catalog)

    assert "label" not in X.columns
    assert "client_id" not in X.columns
    assert "item_id" not in X.columns


def test_build_features_no_score_leakage():
    """Les colonnes *_score de interactions.parquet ne doivent pas atterrir dans X."""
    profiles = _mini_profiles()
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog)
    # Simule la présence de scores dans interactions (comme dans le vrai parquet)
    interactions["color_score"] = 0.5
    interactions["occasion_score"] = 0.5
    interactions["archetype_score"] = 0.5
    interactions["combined_score"] = 0.5

    X, _, _ = build_features(interactions, profiles, catalog)

    for leak in ["color_score", "occasion_score", "archetype_score", "combined_score"]:
        assert leak not in X.columns, f"Leakage : {leak} fuite dans X"


# ============================================================================
# Split
# ============================================================================

def test_group_split_no_client_overlap():
    profiles = _mini_profiles(n=20)
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog, n_per_client=4)

    X, y, groups = build_features(interactions, profiles, catalog)
    (X_tr, _, g_tr), (X_vl, _, g_vl), (X_te, _, g_te) = group_split(
        X, y, groups, val_frac=0.25, test_frac=0.25, seed=42
    )

    train_set = set(g_tr.unique())
    val_set = set(g_vl.unique())
    test_set = set(g_te.unique())

    assert train_set & val_set == set()
    assert train_set & test_set == set()
    assert val_set & test_set == set()
    # Toutes les clientes sont quelque part
    assert train_set | val_set | test_set == set(groups.unique())


def test_group_split_proportions():
    profiles = _mini_profiles(n=100)
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog, n_per_client=3)

    X, y, groups = build_features(interactions, profiles, catalog)
    (_, _, g_tr), (_, _, g_vl), (_, _, g_te) = group_split(
        X, y, groups, val_frac=0.10, test_frac=0.10, seed=42
    )

    n_tr, n_vl, n_te = g_tr.nunique(), g_vl.nunique(), g_te.nunique()
    assert n_tr == 80
    assert n_vl == 10
    assert n_te == 10


def test_group_split_reproducible():
    profiles = _mini_profiles(n=20)
    catalog = _mini_catalog()
    interactions = _mini_interactions(profiles, catalog, n_per_client=3)
    X, y, groups = build_features(interactions, profiles, catalog)

    a = group_split(X, y, groups, seed=42)
    b = group_split(X, y, groups, seed=42)

    pd.testing.assert_frame_equal(a[0][0], b[0][0])
    pd.testing.assert_series_equal(a[0][1], b[0][1])
