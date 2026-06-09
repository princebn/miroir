# scripts/demo_traffic.py
# Genere du trafic /recommend + /feedback pour animer le dashboard Grafana Bloc 4.
from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).resolve().parents[1]
PROFILES = BASE / "data" / "synthetic" / "profiles.parquet"
OCCASIONS = ["bureau", "cocktail", "vacances", "sport", "soiree", "casual"]


def client_ids(n):
    df = pd.read_parquet(PROFILES)
    col = "client_id" if "client_id" in df.columns else df.columns[0]
    ids = df[col].astype(str).tolist()
    random.shuffle(ids)
    return ids[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--n", type=int, default=80)
    ap.add_argument("--clients", type=int, default=40)
    args = ap.parse_args()

    ids = client_ids(args.clients)
    ok = 0
    fb = 0
    lat = []
    for _ in range(args.n):
        cid = random.choice(ids)
        occ = random.choice(OCCASIONS)
        t0 = time.time()
        try:
            r = requests.post(
                args.url + "/recommend",
                json={"client_id": cid, "occasion": occ, "k": 5},
                timeout=10,
            )
        except Exception as e:
            print("recommend KO:", e)
            continue
        lat.append((time.time() - t0) * 1000)
        if r.status_code == 200:
            ok += 1
            items = r.json().get("items", [])
            if items:
                it = random.choice(items)
                action = "approved" if random.random() < 0.6 else "rejected"
                payload = {
                    "client_id": cid,
                    "item_id": it["item_id"],
                    "occasion": occ,
                    "action": action,
                    "score": it.get("score"),
                    "model_version": "2",
                }
                try:
                    rf = requests.post(args.url + "/feedback", json=payload, timeout=10)
                    if rf.status_code in (200, 201):
                        fb += 1
                except Exception as e:
                    print("feedback KO:", e)
        time.sleep(0.05)

    lat.sort()
    p50 = lat[len(lat) // 2] if lat else 0
    p95 = lat[int(len(lat) * 0.95)] if lat else 0
    print("recommend OK:", ok, "/", args.n)
    print("feedback OK:", fb)
    print("latence ms  p50:", round(p50, 1), "p95:", round(p95, 1))


if __name__ == "__main__":
    main()
