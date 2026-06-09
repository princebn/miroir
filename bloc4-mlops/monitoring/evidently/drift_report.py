# monitoring/evidently/drift_report.py
# Rapport de data drift Evidently 0.7.x : reference = train, courant = echantillon.
# HTML + share/count dataset + drift par colonne (Jensen-Shannon), avec verdict.
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

BASE = Path(__file__).resolve().parents[2]
DATA_DIR = BASE / "data" / "synthetic"
DEFAULT_REF = DATA_DIR / "train.parquet"
DEFAULT_CUR = DATA_DIR / "test.parquet"
OUT_DIR = BASE / "monitoring" / "evidently" / "reports"
SENTINELS = ["budget_ord", "taille_ord"]

CAT_COLS = [
    "item_master_category",
    "item_sub_category",
    "item_article_type",
    "item_base_colour",
    "item_season",
    "item_usage",
]


def _load(path):
    df = pd.read_parquet(path)
    return df.drop(columns=["__label", "__client_id"], errors="ignore")


def _data_definition(df):
    onehot = [c for c in df.columns if c.startswith(("morph_", "saison_", "arch_", "occ_"))]
    num = [c for c in ["budget_ord", "taille_ord"] if c in df.columns] + onehot
    cat = [c for c in CAT_COLS if c in df.columns]
    return DataDefinition(numerical_columns=num, categorical_columns=cat)


def _extract_drift(snapshot):
    d = snapshot.dict()
    share = None
    count = None
    columns = {}
    for m in d.get("metrics", []):
        cfg = m.get("config", {})
        mtype = str(cfg.get("type", ""))
        val = m.get("value", None)
        if "DriftedColumnsCount" in mtype and isinstance(val, dict):
            count = val.get("count")
            share = val.get("share")
        elif "ValueDrift" in mtype and isinstance(val, (int, float)):
            col = cfg.get("column")
            thr = cfg.get("threshold", 0.1)
            columns[col] = (float(val), float(thr), float(val) > float(thr))
    return share, count, columns


def simulate_drift(df):
    # [SYNTHETIQUE] perturbe le courant pour une demo de drift franc :
    # sur-representation hiver/automne + clientele plus premium et plus grande.
    out = df.copy()
    if "item_season" in out.columns:
        winter = out[out["item_season"].astype(str).isin(["Winter", "Fall"])]
        base = out.sample(frac=0.2, random_state=0)
        out = pd.concat([winter] * 5 + [base], ignore_index=True)
    for col in ["budget_ord", "taille_ord"]:
        if col in out.columns:
            out[col] = (out[col] + 1).clip(upper=int(out[col].max()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", default=str(DEFAULT_REF))
    ap.add_argument("--current", default=str(DEFAULT_CUR))
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--share-threshold", type=float, default=0.2)
    args = ap.parse_args()

    ref = _load(args.reference)
    cur = _load(args.current)
    if args.simulate:
        cur = simulate_drift(cur)

    cols = [c for c in ref.columns if c in cur.columns]
    ref = ref[cols]
    cur = cur[cols]

    dd = _data_definition(ref)
    ref_ds = Dataset.from_pandas(ref, data_definition=dd)
    cur_ds = Dataset.from_pandas(cur, data_definition=dd)

    snap = Report(metrics=[DataDriftPreset()]).run(current_data=cur_ds, reference_data=ref_ds)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "drift" if args.simulate else "stable"
    html_path = OUT_DIR / ("data_drift_" + suffix + ".html")
    snap.save_html(str(html_path))

    share, count, columns = _extract_drift(snap)
    drifted = {c: v for c, (v, t, f) in columns.items() if f}
    sentinels_hit = [c for c in SENTINELS if columns.get(c, (0.0, 0.0, False))[2]]
    flag = "  [SIMULE]" if args.simulate else ""

    print("Reference :", args.reference, "(" + str(len(ref)) + " lignes)")
    print("Courant   :", args.current, "(" + str(len(cur)) + " lignes)" + flag)
    print("Colonnes analysees :", len(cols))
    print("Share colonnes driftees (dataset) :", share)
    print("Nb colonnes driftees :", count)
    print("Features sentinelles en drift :", sentinels_hit if sentinels_hit else "aucune")
    if drifted:
        top = sorted(drifted.items(), key=lambda kv: kv[1], reverse=True)[:5]
        print("Top colonnes driftees (Jensen-Shannon) :")
        for name, v in top:
            print("  -", name, ":", round(v, 3))
    print("Rapport HTML :", html_path)

    is_drift = (share is not None and share > args.share_threshold) or len(sentinels_hit) > 0
    if is_drift:
        print("VERDICT : DRIFT DETECTE -> reentrainement recommande")
    else:
        print("VERDICT : pas de drift significatif")


if __name__ == "__main__":
    main()
