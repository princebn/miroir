"""
tests/test_interactions.py

Tests des règles de compatibilité (compatibility.py) et du générateur
d'interactions (generate_interactions.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.synth.compatibility import (
    APPROVAL_THRESHOLD,
    ARCHETYPE_ARTICLE_TYPES,
    OCCASION_USAGES,
    SAISON_PALETTES,
    archetype_score,
    color_score,
    combined_score,
    occasion_score,
)
from src.synth.generate_interactions import generate_interactions


# ============================================================================
# Couverture des mappings
# ============================================================================

def test_all_12_saisons_have_palette():
    expected = {
        "printemps_clair", "printemps_chaud", "printemps_lumineux",
        "ete_doux", "ete_froid", "ete_lumineux",
        "automne_chaud", "automne_profond", "automne_doux",
        "hiver_froid", "hiver_profond", "hiver_lumineux",
    }
    assert set(SAISON_PALETTES.keys()) == expected


def test_tier1_and_tier2_disjoint_per_saison():
    for saison, (t1, t2) in SAISON_PALETTES.items():
        overlap = t1 & t2
        assert overlap == set(), f"{saison} : chevauchement tier1/tier2 sur {overlap}"


def test_each_saison_has_minimum_colors():
    """Chaque saison a au moins 6 couleurs tier 1 (palette signature minimale)."""
    for saison, (t1, _) in SAISON_PALETTES.items():
        assert len(t1) >= 6, f"{saison} : seulement {len(t1)} couleurs signatures"


def test_all_6_occasions_mapped():
    assert set(OCCASION_USAGES.keys()) == {
        "bureau", "cocktail", "vacances", "sport", "soiree", "casual",
    }


def test_all_6_archetypes_mapped():
    assert set(ARCHETYPE_ARTICLE_TYPES.keys()) == {
        "classique", "naturel", "romantique", "dramatique", "creatif", "elegant_chic",
    }


# ============================================================================
# Scoring : sanity
# ============================================================================

def test_color_score_signature_is_one():
    """Une couleur tier 1 d'une saison donne 1.0."""
    # Coral est signature de printemps_clair
    assert color_score("Coral", "printemps_clair") == 1.0


def test_color_score_secondary_is_six():
    """Une couleur tier 2 d'une saison donne 0.6."""
    # Yellow est tier 2 de printemps_clair
    assert color_score("Yellow", "printemps_clair") == 0.6


def test_color_score_off_palette_is_low():
    """Une couleur absente du tier1+tier2 d'une saison donne 0.1."""
    # Burgundy n'est ni signature ni compatible pour printemps_clair
    assert color_score("Burgundy", "printemps_clair") == 0.1


def test_color_score_handles_none_and_multi():
    """None et Multi/Metallic donnent un score neutre."""
    assert color_score(None, "printemps_clair") == 0.4
    assert color_score("Multi", "printemps_clair") == 0.4


def test_occasion_score_match():
    assert occasion_score("Sports", "sport") == 1.0
    assert occasion_score("Formal", "bureau") == 1.0
    assert occasion_score("Casual", "vacances") == 1.0


def test_occasion_score_mismatch():
    assert occasion_score("Sports", "cocktail") < 0.5
    assert occasion_score("Formal", "sport") < 0.5


def test_archetype_score_matches_at_least_one():
    """Si un seul archétype de la cliente matche, score = 1."""
    assert archetype_score("Dresses", ["romantique"]) == 1.0
    assert archetype_score("Dresses", ["classique", "romantique"]) == 1.0


def test_archetype_score_no_match_falls_back():
    """Aucun archétype ne matche → fallback 0.4 (pas exclu)."""
    assert archetype_score("Boots", ["naturel"]) == 0.4


# ============================================================================
# Score combiné
# ============================================================================

def test_combined_score_bounds():
    cs, os_, as_, comb = combined_score(
        color="Burgundy", usage="Sports", article_type="Boots",
        saison="printemps_clair", occasion="bureau", archetypes=["naturel"],
    )
    assert 0.0 <= comb <= 1.0
    assert 0.0 <= cs <= 1.0 and 0.0 <= os_ <= 1.0 and 0.0 <= as_ <= 1.0


def test_combined_score_aligned_returns_high():
    """Article totalement aligné avec le profil → score haut."""
    cs, os_, as_, comb = combined_score(
        color="Coral", usage="Sports", article_type="Sneakers",
        saison="printemps_clair", occasion="sport", archetypes=["naturel"],
    )
    assert comb >= APPROVAL_THRESHOLD


# ============================================================================
# Générateur — sur un mini catalogue
# ============================================================================

def _make_mini_catalog() -> pd.DataFrame:
    """Catalogue jouet de 20 articles pour les tests."""
    rng = np.random.default_rng(0)
    n = 20
    colors = ["Coral", "Black", "Navy Blue", "Burgundy", "Yellow", "Pink",
              "White", "Brown", "Olive", "Grey"]
    types  = ["Tshirts", "Dresses", "Sneakers", "Heels", "Jeans", "Boots", "Tunics"]
    usages = ["Casual", "Sports", "Formal", "Party", "Smart Casual"]
    return pd.DataFrame({
        "item_id": [f"it{i:03d}" for i in range(n)],
        "gender": ["Women"] * n,
        "master_category": ["Apparel"] * n,
        "sub_category": ["Topwear"] * n,
        "article_type": rng.choice(types, size=n),
        "base_colour": rng.choice(colors, size=n),
        "season": ["Summer"] * n,
        "usage": rng.choice(usages, size=n),
        "product_display_name": [f"Article {i}" for i in range(n)],
    })


def _make_mini_profiles(n: int = 5) -> pd.DataFrame:
    return pd.DataFrame({
        "client_id": [f"c{i:03d}" for i in range(n)],
        "consultante_id": ["k1"] * n,
        "morphologie": ["sablier"] * n,
        "saison_colorimetrique": [
            "printemps_clair", "hiver_froid", "automne_chaud",
            "ete_doux", "printemps_lumineux"
        ][:n],
        "archetypes": [["naturel"], ["classique"], ["romantique"], ["elegant_chic"], ["creatif"]][:n],
        "budget_tranche": ["milieu_bas"] * n,
        "occasions": [["bureau", "casual"]] * n,
        "taille": ["M"] * n,
    })


def test_generator_reproducible():
    catalog = _make_mini_catalog()
    profiles = _make_mini_profiles()
    a = generate_interactions(profiles, catalog, per_client=10, seed=42)
    b = generate_interactions(profiles, catalog, per_client=10, seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_generator_volume_matches():
    catalog = _make_mini_catalog()
    profiles = _make_mini_profiles(n=5)
    df = generate_interactions(profiles, catalog, per_client=10, seed=42)
    assert len(df) == 5 * 10


def test_generator_labels_are_binary():
    catalog = _make_mini_catalog()
    profiles = _make_mini_profiles()
    df = generate_interactions(profiles, catalog, per_client=10, seed=42)
    assert set(df["label"].unique()) <= {0, 1}


def test_generator_occasions_from_client_only():
    catalog = _make_mini_catalog()
    profiles = _make_mini_profiles()
    df = generate_interactions(profiles, catalog, per_client=10, seed=42)
    # Toutes les profils ont occasions = ["bureau", "casual"]
    assert set(df["occasion"].unique()) <= {"bureau", "casual"}


def test_generator_no_internal_duplicates_per_client():
    """Pour une cliente donnée, pas deux fois le même item_id."""
    catalog = _make_mini_catalog()
    profiles = _make_mini_profiles()
    df = generate_interactions(profiles, catalog, per_client=10, seed=42)
    for client_id, g in df.groupby("client_id"):
        assert g["item_id"].is_unique, f"doublons pour {client_id}"


def test_generator_label_balance_in_range():
    """Sur un mini-catalogue varié, le taux d'approbation reste raisonnable (5–80 %)."""
    catalog = _make_mini_catalog()
    profiles = _make_mini_profiles()
    df = generate_interactions(profiles, catalog, per_client=15, seed=42)
    rate = df["label"].mean()
    assert 0.05 <= rate <= 0.80, f"taux d'approbation hors plage : {rate:.2%}"
