"""
src/reranker/split.py

Split train / validation / test PAR CLIENTE.

Le split par cliente (et non par interaction) est essentiel : il évite la
fuite. Un modèle qui apprend les préférences spécifiques d'une cliente vue
à la fois en train et en eval donnerait une métrique gonflée mais sans
valeur en production où chaque cliente est nouvelle pour le modèle.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SplitTriplet = tuple[pd.DataFrame, pd.Series, pd.Series]


def group_split(
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
    val_frac: float = 0.10,
    test_frac: float = 0.10,
    seed: int = 42,
) -> tuple[SplitTriplet, SplitTriplet, SplitTriplet]:
    """Split par identifiant de groupe (typiquement client_id).

    Args:
        X         : features
        y         : labels (même index que X)
        groups    : identifiant de groupe par row
        val_frac  : fraction des clientes en validation
        test_frac : fraction des clientes en test
        seed      : graine pour la reproductibilité

    Returns:
        (X_tr, y_tr, g_tr), (X_vl, y_vl, g_vl), (X_te, y_te, g_te)
    """
    rng = np.random.default_rng(seed)

    unique_clients = np.array(groups.unique(), copy=True)
    rng.shuffle(unique_clients)

    n_total = len(unique_clients)
    n_test = int(n_total * test_frac)
    n_val = int(n_total * val_frac)

    test_clients = set(unique_clients[:n_test])
    val_clients = set(unique_clients[n_test : n_test + n_val])
    train_clients = set(unique_clients[n_test + n_val :])

    def _slice(mask: pd.Series) -> SplitTriplet:
        return (
            X.loc[mask].reset_index(drop=True),
            y.loc[mask].reset_index(drop=True),
            groups.loc[mask].reset_index(drop=True),
        )

    return (
        _slice(groups.isin(train_clients)),
        _slice(groups.isin(val_clients)),
        _slice(groups.isin(test_clients)),
    )
