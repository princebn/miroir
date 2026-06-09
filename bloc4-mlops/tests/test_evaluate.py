"""
tests/test_evaluate.py

Tests des métriques d'évaluation du re-ranker (evaluate.py).
"""

from __future__ import annotations

import numpy as np
import pytest

from src.reranker.evaluate import (
    evaluate_classification,
    evaluate_ranking,
    ndcg_at_k,
    recall_at_k,
)

# ============================================================================
# NDCG@K
# ============================================================================


def test_ndcg_perfect_ranking_is_one():
    """Tous les positifs en tête → NDCG = 1."""
    scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
    labels = np.array([1, 1, 1, 0, 0])
    assert ndcg_at_k(scores, labels, 3) == pytest.approx(1.0)


def test_ndcg_worst_ranking_is_lower_than_perfect():
    """Positifs en queue → NDCG < 1."""
    scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
    labels = np.array([0, 0, 1, 1, 1])
    n = ndcg_at_k(scores, labels, 3)
    assert 0 < n < 1.0


def test_ndcg_returns_zero_when_no_positives():
    scores = np.array([0.9, 0.8, 0.7])
    labels = np.array([0, 0, 0])
    assert ndcg_at_k(scores, labels, 3) == 0.0


def test_ndcg_at_k_truncates_correctly():
    """NDCG@K ne doit considérer que les K premiers."""
    scores = np.array([0.9, 0.5, 0.1])
    labels = np.array([1, 1, 1])
    # K=1 : un seul positif en tête, ideal = 1 positif aussi → ratio = 1
    assert ndcg_at_k(scores, labels, 1) == pytest.approx(1.0)


# ============================================================================
# Recall@K
# ============================================================================


def test_recall_perfect():
    scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
    labels = np.array([1, 1, 1, 0, 0])
    assert recall_at_k(scores, labels, 3) == pytest.approx(1.0)


def test_recall_zero_when_top_misses_all_positives():
    """Le top-K est entièrement composé de négatifs."""
    scores = np.array([0.1, 0.2, 0.9, 0.95, 0.8])
    labels = np.array([1, 1, 0, 0, 0])
    # Top 2 par score = positions 3, 4 (0.95, 0.8) → tous deux 0 → recall = 0
    assert recall_at_k(scores, labels, 2) == 0.0


def test_recall_returns_none_when_no_positives():
    scores = np.array([0.9, 0.8])
    labels = np.array([0, 0])
    assert recall_at_k(scores, labels, 2) is None


def test_recall_partial_coverage():
    """3 positifs, on en attrape 2 dans le top → recall = 2/3."""
    scores = np.array([0.9, 0.8, 0.1, 0.05])
    labels = np.array([1, 1, 1, 0])
    assert recall_at_k(scores, labels, 2) == pytest.approx(2.0 / 3.0)


# ============================================================================
# evaluate_ranking — groupement
# ============================================================================


def test_evaluate_ranking_two_groups_both_perfect():
    """Deux groupes, chacun avec un ranking parfait → métriques = 1."""
    y_pred = np.array([0.9, 0.5, 0.1, 0.1, 0.5, 0.9])
    y_true = np.array([1, 0, 0, 0, 0, 1])
    groups = np.array(["a", "a", "a", "b", "b", "b"])

    m = evaluate_ranking(y_pred, y_true, groups, ks=(1, 3))
    assert m["ndcg_at_1"] == pytest.approx(1.0)
    assert m["recall_at_1"] == pytest.approx(1.0)
    assert m["n_groups"] == 2.0
    assert m["n_groups_with_positive"] == 2.0


def test_evaluate_ranking_excludes_no_positive_groups_from_recall_mean():
    """Un groupe sans positif est exclu du recall (mais compté dans n_groups)."""
    y_pred = np.array([0.9, 0.5, 0.9, 0.5])
    y_true = np.array([1, 0, 0, 0])
    groups = np.array(["a", "a", "b", "b"])

    m = evaluate_ranking(y_pred, y_true, groups, ks=(1,))
    # Seulement le groupe 'a' a un positif
    assert m["n_groups"] == 2.0
    assert m["n_groups_with_positive"] == 1.0
    # Recall sur 'a' seul = 1.0
    assert m["recall_at_1"] == pytest.approx(1.0)


# ============================================================================
# evaluate_classification
# ============================================================================


def test_evaluate_classification_returns_expected_keys():
    y_pred = np.array([0.1, 0.4, 0.8, 0.9])
    y_true = np.array([0, 0, 1, 1])
    m = evaluate_classification(y_pred, y_true)
    for key in ["auc", "average_precision", "f1", "precision_at_0_5", "recall_at_0_5"]:
        assert key in m


def test_evaluate_classification_perfect_separator():
    """Prédictions parfaitement séparées → AUC = 1."""
    y_pred = np.array([0.1, 0.2, 0.8, 0.9])
    y_true = np.array([0, 0, 1, 1])
    m = evaluate_classification(y_pred, y_true)
    assert m["auc"] == pytest.approx(1.0)
    assert m["average_precision"] == pytest.approx(1.0)


def test_evaluate_classification_handles_constant_pred_below_threshold():
    """Toutes les prédictions sous 0.5 → precision/recall = 0, pas d'erreur."""
    y_pred = np.array([0.1, 0.2, 0.3, 0.4])
    y_true = np.array([0, 0, 1, 1])
    m = evaluate_classification(y_pred, y_true)
    assert m["precision_at_0_5"] == 0.0
    assert m["recall_at_0_5"] == 0.0
