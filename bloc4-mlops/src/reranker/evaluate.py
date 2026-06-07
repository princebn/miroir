"""
src/reranker/evaluate.py

Métriques d'évaluation du re-ranker.

Deux familles :
1. Classification (sur tout le set, indépendant du regroupement)
   - AUC ROC
   - Average Precision (PR-AUC, robuste à l'imbalance)
   - F1, precision, recall au seuil 0.5
2. Ranking (groupé par (cliente, occasion))
   - NDCG@K  : reflète la position des bons articles dans la short-list
   - Recall@K : fraction des approuvés que le modèle met dans le top-K

Pour le ranking, on exclut les groupes sans positif (recall mal défini).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def ndcg_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """NDCG@K pour un groupe, relevance binaire.

    DCG@K  = Σ (2^rel_i - 1) / log2(i + 1)   pour i ∈ [1..K]
    IDCG@K = DCG@K pour l'ordre idéal
    NDCG@K = DCG@K / IDCG@K  ∈ [0, 1]
    """
    if labels.sum() == 0:
        return 0.0
    order = np.argsort(-scores)
    ranked = labels[order][:k]
    discounts = 1.0 / np.log2(np.arange(2, len(ranked) + 2))
    dcg = float((ranked * discounts).sum())

    ideal = np.sort(labels)[::-1][:k]
    idiscounts = 1.0 / np.log2(np.arange(2, len(ideal) + 2))
    idcg = float((ideal * idiscounts).sum())

    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float | None:
    """Recall@K pour un groupe. Retourne None si aucun positif dans le groupe."""
    if labels.sum() == 0:
        return None
    order = np.argsort(-scores)
    ranked = labels[order][:k]
    return float(ranked.sum() / labels.sum())


def evaluate_ranking(
    y_pred: np.ndarray,
    y_true: np.ndarray,
    group_keys: np.ndarray,
    ks: tuple[int, ...] = (1, 3, 5),
) -> dict[str, float]:
    """Calcule NDCG@K et Recall@K pour chaque groupe, retourne les moyennes.

    Args:
        y_pred    : scores prédits, shape (N,)
        y_true    : labels binaires, shape (N,)
        group_keys: clé de groupement, shape (N,) — typiquement "client_id|occasion"
        ks        : valeurs de K à évaluer
    """
    df = pd.DataFrame({"pred": y_pred, "label": y_true, "key": group_keys})

    ndcg_acc: dict[int, list[float]] = {k: [] for k in ks}
    recall_acc: dict[int, list[float]] = {k: [] for k in ks}

    for _, g in df.groupby("key", sort=False):
        scores = g["pred"].to_numpy()
        labels = g["label"].to_numpy()
        for k in ks:
            ndcg_acc[k].append(ndcg_at_k(scores, labels, k))
            r = recall_at_k(scores, labels, k)
            if r is not None:
                recall_acc[k].append(r)

    metrics: dict[str, float] = {}
    for k in ks:
        metrics[f"ndcg_at_{k}"] = float(np.mean(ndcg_acc[k])) if ndcg_acc[k] else 0.0
        metrics[f"recall_at_{k}"] = float(np.mean(recall_acc[k])) if recall_acc[k] else 0.0
    metrics["n_groups"] = float(df["key"].nunique())
    metrics["n_groups_with_positive"] = float(len(recall_acc[ks[0]]))
    return metrics


def evaluate_classification(y_pred: np.ndarray, y_true: np.ndarray) -> dict[str, float]:
    """Métriques de classification standards."""
    y_pred_bin = (y_pred > 0.5).astype(int)
    return {
        "auc": float(roc_auc_score(y_true, y_pred)),
        "average_precision": float(average_precision_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred_bin, zero_division=0)),
        "precision_at_0_5": float(precision_score(y_true, y_pred_bin, zero_division=0)),
        "recall_at_0_5": float(recall_score(y_true, y_pred_bin, zero_division=0)),
    }
