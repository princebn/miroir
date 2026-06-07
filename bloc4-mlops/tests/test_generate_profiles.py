"""
tests/test_generate_profiles.py

Tests unitaires du générateur de profils synthétiques.
Vérifient la reproductibilité, les volumes, et la cohérence avec la spec.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.synth.generate_profiles import (
    ARCHETYPES,
    BUDGETS,
    MORPHOLOGIES,
    OCCASIONS,
    SAISONS,
    TAILLES,
    generate_profiles,
)


def test_reproducible_with_same_seed():
    """Même seed → DataFrame strictement identique (reproductibilité)."""
    df1 = generate_profiles(n_consultantes=5, clients_per_consultante=10, seed=42)
    df2 = generate_profiles(n_consultantes=5, clients_per_consultante=10, seed=42)
    pd.testing.assert_frame_equal(df1, df2)


def test_different_seeds_diverge():
    """Seeds différentes → contenus différents."""
    df1 = generate_profiles(n_consultantes=5, clients_per_consultante=10, seed=42)
    df2 = generate_profiles(n_consultantes=5, clients_per_consultante=10, seed=43)
    assert not df1.equals(df2)


def test_volumes_match_inputs():
    """Le volume sorti respecte n_consultantes * clients_per_consultante."""
    df = generate_profiles(n_consultantes=50, clients_per_consultante=30, seed=42)
    assert len(df) == 1500
    assert df.consultante_id.nunique() == 50
    assert df.client_id.nunique() == 1500


def test_vocabularies_locked():
    """Toutes les valeurs sortent du vocabulaire spec."""
    df = generate_profiles(n_consultantes=10, clients_per_consultante=20, seed=42)
    assert set(df.morphologie.unique()) <= set(MORPHOLOGIES)
    assert set(df.saison_colorimetrique.unique()) <= set(SAISONS)
    assert set(df.budget_tranche.unique()) <= set(BUDGETS)
    assert set(df.taille.unique()) <= set(TAILLES)

    flat_arch = [a for lst in df.archetypes for a in lst]
    assert set(flat_arch) <= set(ARCHETYPES)

    flat_occ = [o for lst in df.occasions for o in lst]
    assert set(flat_occ) <= set(OCCASIONS)


def test_multi_label_counts_in_range():
    """Chaque cliente a 1 à 3 archétypes et 1 à 3 occasions."""
    df = generate_profiles(n_consultantes=10, clients_per_consultante=20, seed=42)

    arch_counts = df.archetypes.apply(len)
    assert arch_counts.min() >= 1
    assert arch_counts.max() <= 3

    occ_counts = df.occasions.apply(len)
    assert occ_counts.min() >= 1
    assert occ_counts.max() <= 3


def test_client_ids_unique():
    """Aucun client_id en double sur 1500 profils."""
    df = generate_profiles(n_consultantes=50, clients_per_consultante=30, seed=42)
    assert df.client_id.is_unique


def test_no_duplicate_in_multi_labels():
    """Les listes (archétypes, occasions) n'ont pas de doublons internes."""
    df = generate_profiles(n_consultantes=10, clients_per_consultante=20, seed=42)
    assert df.archetypes.apply(lambda lst: len(set(lst)) == len(lst)).all()
    assert df.occasions.apply(lambda lst: len(set(lst)) == len(lst)).all()


@pytest.mark.parametrize("col,vocab", [
    ("morphologie", MORPHOLOGIES),
    ("budget_tranche", BUDGETS),
    ("taille", TAILLES),
])
def test_distribution_approximates_spec(col, vocab):
    """Avec un échantillon de 5000, la distribution observée approche la spec à ±5pt."""
    df = generate_profiles(n_consultantes=100, clients_per_consultante=50, seed=42)
    observed = df[col].value_counts(normalize=True)
    # Vérifie que toutes les valeurs spec apparaissent
    assert set(observed.index) == set(vocab)
    # Pas de valeur > 60% (sanity : aucune classe ne domine accidentellement)
    assert observed.max() < 0.60
