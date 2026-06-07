"""
src/reranker/train.py

Entraîne plusieurs configurations LightGBM, log chaque run dans MLflow,
sélectionne la meilleure sur val AUC, évalue sur test, enregistre dans le
Model Registry sous le nom `miroir_reranker`.

Usage :
    python -m src.reranker.train

Pour visualiser après :
    mlflow ui --backend-store-uri sqlite:///bloc4-mlops/mlflow.db
    (puis ouvrir http://localhost:5000)
"""
from __future__ import annotations

import os
from pathlib import Path

import lightgbm as lgb
import mlflow
import mlflow.lightgbm
import numpy as np
import pandas as pd

from src.reranker.evaluate import evaluate_classification, evaluate_ranking
from src.reranker.features import ITEM_CATEGORICAL_COLS, OCCASIONS


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
TRAIN_PATH = DATA_DIR / "train.parquet"
VAL_PATH = DATA_DIR / "val.parquet"
TEST_PATH = DATA_DIR / "test.parquet"

MLFLOW_DB = Path(__file__).resolve().parents[2] / "mlflow.db"
TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB}")
EXPERIMENT_NAME = "miroir-reranker"
REGISTERED_MODEL_NAME = "miroir_reranker"


# Configurations comparées — variations modérées, faciles à interpréter
CONFIGS: list[dict] = [
    {"name": "baseline",      "learning_rate": 0.10, "num_leaves":  31, "min_child_samples": 20},
    {"name": "deeper",        "learning_rate": 0.10, "num_leaves":  63, "min_child_samples": 20},
    {"name": "slower",        "learning_rate": 0.05, "num_leaves":  31, "min_child_samples": 50},
    {"name": "deeper_slower", "learning_rate": 0.05, "num_leaves":  63, "min_child_samples": 50},
]


# ============================================================================
# Helpers
# ============================================================================

def _load_split(path: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    df = pd.read_parquet(path)
    y = df.pop("__label").astype(int)
    g = df.pop("__client_id")
    return df, y, g


def _prepare_for_lightgbm(X: pd.DataFrame) -> pd.DataFrame:
    """Convertit les colonnes catégoriques string en category dtype."""
    X = X.copy()
    for col in ITEM_CATEGORICAL_COLS:
        X[col] = X[col].astype("category")
    return X


def _reconstruct_occasion(X: pd.DataFrame) -> np.ndarray:
    """Reconstitue l'occasion (str) depuis les colonnes one-hot occ_*."""
    occ_cols = [f"occ_{o}" for o in OCCASIONS]
    idx = X[occ_cols].values.argmax(axis=1)
    return np.array([OCCASIONS[i] for i in idx])


def _group_key(client_ids: pd.Series, occasions: np.ndarray) -> np.ndarray:
    return np.array([f"{c}|{o}" for c, o in zip(client_ids.values, occasions)])


def _log_feature_importance_plot(model: lgb.LGBMClassifier, feature_names: list[str],
                                  config_name: str) -> None:
    """Génère et logge un plot des 20 features les plus importantes."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return  # matplotlib indisponible, on saute

    fi = pd.DataFrame({"feature": feature_names, "importance": model.feature_importances_})
    fi = fi.sort_values("importance", ascending=True).tail(20)

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(fi["feature"], fi["importance"], color="#B8956A")
    ax.set_xlabel("Importance (gain)")
    ax.set_title(f"Top 20 features — {config_name}")
    plt.tight_layout()

    tmp = Path("/tmp") / f"fi_{config_name}.png"
    plt.savefig(tmp, dpi=120)
    plt.close(fig)
    mlflow.log_artifact(str(tmp), "feature_importance")


# ============================================================================
# Train one config
# ============================================================================

def train_one(config: dict, X_tr, y_tr, g_tr, X_vl, y_vl, g_vl) -> tuple[lgb.LGBMClassifier, dict, str]:
    """Entraîne une config, log dans MLflow, retourne (modèle, métriques val, run_id)."""
    pos = int(y_tr.sum())
    neg = int(len(y_tr) - pos)
    scale_pos_weight = neg / max(pos, 1)

    params = {
        "objective":          "binary",
        "learning_rate":      config["learning_rate"],
        "num_leaves":         config["num_leaves"],
        "min_child_samples":  config["min_child_samples"],
        "scale_pos_weight":   scale_pos_weight,
        "n_estimators":       500,
        "random_state":       42,
        "verbose":            -1,
    }

    with mlflow.start_run(run_name=config["name"]) as run:
        mlflow.log_params({
            **config,
            "scale_pos_weight": round(scale_pos_weight, 3),
            "n_estimators":     params["n_estimators"],
            "train_rows":       len(X_tr),
            "val_rows":         len(X_vl),
            "n_features":       X_tr.shape[1],
        })

        Xtr_p = _prepare_for_lightgbm(X_tr)
        Xvl_p = _prepare_for_lightgbm(X_vl)

        model = lgb.LGBMClassifier(**params)
        model.fit(
            Xtr_p, y_tr,
            eval_set=[(Xvl_p, y_vl)],
            categorical_feature=ITEM_CATEGORICAL_COLS,
            callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(0)],
        )

        y_pred_vl = model.predict_proba(Xvl_p)[:, 1]
        cls = evaluate_classification(y_pred_vl, y_vl.to_numpy())

        occ_vl = _reconstruct_occasion(X_vl)
        gk_vl = _group_key(g_vl, occ_vl)
        rank = evaluate_ranking(y_pred_vl, y_vl.to_numpy(), gk_vl, ks=(1, 3, 5))

        mlflow.log_metrics({f"val_{k}": v for k, v in {**cls, **rank}.items()})
        mlflow.log_metric("val_best_iteration", float(model.best_iteration_ or model.n_estimators))

        _log_feature_importance_plot(model, list(Xtr_p.columns), config["name"])

        mlflow.lightgbm.log_model(model, name="model")

        all_metrics = {**cls, **rank}
        return model, all_metrics, run.info.run_id


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    print(f"Tracking URI : {TRACKING_URI}")
    print(f"Experiment    : {EXPERIMENT_NAME}")
    print()

    X_tr, y_tr, g_tr = _load_split(TRAIN_PATH)
    X_vl, y_vl, g_vl = _load_split(VAL_PATH)
    X_te, y_te, g_te = _load_split(TEST_PATH)

    print(f"Train : {X_tr.shape}  positifs : {int(y_tr.sum()):,}  taux : {y_tr.mean():.1%}")
    print(f"Val   : {X_vl.shape}  positifs : {int(y_vl.sum()):,}  taux : {y_vl.mean():.1%}")
    print(f"Test  : {X_te.shape}  positifs : {int(y_te.sum()):,}  taux : {y_te.mean():.1%}")

    results: list[tuple[str, lgb.LGBMClassifier, dict, str]] = []
    for cfg in CONFIGS:
        print(f"\n=== Run : {cfg['name']} ===")
        model, metrics, run_id = train_one(cfg, X_tr, y_tr, g_tr, X_vl, y_vl, g_vl)
        print(f"  AUC = {metrics['auc']:.4f}   "
              f"AP = {metrics['average_precision']:.4f}   "
              f"NDCG@5 = {metrics['ndcg_at_5']:.4f}   "
              f"Recall@5 = {metrics['recall_at_5']:.4f}")
        results.append((cfg["name"], model, metrics, run_id))

    # Sélection : meilleur val AUC
    best_name, best_model, best_metrics_val, best_run_id = max(results, key=lambda r: r[2]["auc"])
    print(f"\n=== Meilleur modèle (val AUC) : {best_name}  AUC = {best_metrics_val['auc']:.4f} ===")

    # Évaluation finale sur TEST
    X_te_p = _prepare_for_lightgbm(X_te)
    y_pred_te = best_model.predict_proba(X_te_p)[:, 1]
    cls_te = evaluate_classification(y_pred_te, y_te.to_numpy())
    occ_te = _reconstruct_occasion(X_te)
    gk_te = _group_key(g_te, occ_te)
    rank_te = evaluate_ranking(y_pred_te, y_te.to_numpy(), gk_te, ks=(1, 3, 5))

    print(f"\nMétriques TEST :")
    print(f"  AUC          : {cls_te['auc']:.4f}")
    print(f"  AP (PR-AUC)  : {cls_te['average_precision']:.4f}")
    print(f"  F1 @ 0.5     : {cls_te['f1']:.4f}")
    print(f"  NDCG@1 / @3 / @5 : "
          f"{rank_te['ndcg_at_1']:.4f} / {rank_te['ndcg_at_3']:.4f} / {rank_te['ndcg_at_5']:.4f}")
    print(f"  Recall@1 / @3 / @5 : "
          f"{rank_te['recall_at_1']:.4f} / {rank_te['recall_at_3']:.4f} / {rank_te['recall_at_5']:.4f}")
    print(f"  Groupes (cliente × occasion) : {int(rank_te['n_groups']):,} "
          f"dont {int(rank_te['n_groups_with_positive']):,} avec au moins un positif")

    # Logging des métriques test sur la run gagnante
    with mlflow.start_run(run_id=best_run_id):
        mlflow.log_metrics({f"test_{k}": v for k, v in {**cls_te, **rank_te}.items()})

    # Enregistrement Model Registry
    print(f"\nEnregistrement dans le Model Registry sous `{REGISTERED_MODEL_NAME}`…")
    try:
        result = mlflow.register_model(
            f"runs:/{best_run_id}/model",
            REGISTERED_MODEL_NAME,
        )
        print(f"  ✓ Version créée : {result.version}")
    except Exception as e:
        print(f"  Avertissement : enregistrement échoué — {e}")

    print(f"\nPour inspecter les runs : mlflow ui --backend-store-uri {TRACKING_URI}")


if __name__ == "__main__":
    main()
