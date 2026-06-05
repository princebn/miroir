#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Miroir — Exploration factuelle des datasets (Bloc 2).
Profile H&M (transactions/articles/customers) + Fashion Product Images.
Imprime un rapport ET l'écrit dans docs/data_profile.md.
Aucun chiffre inventé : tout vient des fichiers réels.
"""
import os, sys, datetime

HOME = os.path.expanduser("~")
FASHION_DIR = os.path.join(HOME, "Downloads", "archive fashion")
HM_DIR = os.path.join(HOME, "Downloads", "h-and-m-personalized-fashion-recommendations")
STYLES = os.path.join(FASHION_DIR, "styles.csv")
IMAGES = os.path.join(FASHION_DIR, "images")
TX = os.path.join(HM_DIR, "transactions_train.csv")
ARTICLES = os.path.join(HM_DIR, "articles.csv")
CUSTOMERS = os.path.join(HM_DIR, "customers.csv")

OUT = []
def p(*a):
    line = " ".join(str(x) for x in a)
    print(line); OUT.append(line)

def section(t):
    p("\n" + "=" * 64); p(t); p("=" * 64)

def fsize(path):
    try: return f"{os.path.getsize(path)/1e9:.2f} Go" if os.path.getsize(path) > 1e9 else f"{os.path.getsize(path)/1e6:.1f} Mo"
    except Exception: return "??"

p("MIROIR — PROFIL DES DONNÉES  ·", datetime.date.today().isoformat())

# ---------------------------------------------------------------- H&M
try:
    import polars as pl
    section("H&M — transactions_train.csv  (" + fsize(TX) + ")")
    tx = pl.scan_csv(TX, infer_schema_length=10000)
    g = tx.select(
        pl.len().alias("n_rows"),
        pl.col("t_dat").min().alias("date_min"),
        pl.col("t_dat").max().alias("date_max"),
        pl.col("customer_id").n_unique().alias("n_customers"),
        pl.col("article_id").n_unique().alias("n_articles"),
        pl.col("price").min().alias("price_min"),
        pl.col("price").mean().alias("price_mean"),
        pl.col("price").median().alias("price_median"),
        pl.col("price").quantile(0.9).alias("price_p90"),
        pl.col("price").max().alias("price_max"),
    ).collect(streaming=True).to_dicts()[0]
    n = g["n_rows"]
    d0 = datetime.date.fromisoformat(g["date_min"]); d1 = datetime.date.fromisoformat(g["date_max"])
    ndays = (d1 - d0).days + 1
    p(f"lignes (transactions) ............ {n:,}".replace(",", " "))
    p(f"période .......................... {g['date_min']} → {g['date_max']}  ({ndays} jours)")
    p(f"clients distincts ................ {g['n_customers']:,}".replace(",", " "))
    p(f"articles distincts ............... {g['n_articles']:,}".replace(",", " "))
    p(f"moyenne transactions / jour ...... {n//ndays:,}".replace(",", " "))
    p(f"prix (unité dataset, normalisé) .. min={g['price_min']:.5f}  médiane={g['price_median']:.5f}  moy={g['price_mean']:.5f}  p90={g['price_p90']:.5f}  max={g['price_max']:.5f}")
    chan = tx.group_by("sales_channel_id").agg(pl.len().alias("n")).sort("sales_channel_id").collect(streaming=True)
    p("canaux de vente (sales_channel_id) :")
    for r in chan.to_dicts(): p(f"   canal {r['sales_channel_id']} : {r['n']:,}".replace(",", " "))
    monthly = (tx.with_columns(pl.col("t_dat").str.slice(0, 7).alias("ym"))
               .group_by("ym").agg(pl.len().alias("n")).sort("ym").collect(streaming=True))
    p("volume par mois (saisonnalité) :")
    for r in monthly.to_dicts(): p(f"   {r['ym']} : {r['n']:,}".replace(",", " "))

    section("H&M — articles.csv  (" + fsize(ARTICLES) + ")")
    art = pl.read_csv(ARTICLES, infer_schema_length=10000)
    p(f"lignes (articles) ................ {art.height:,}".replace(",", " "))
    p(f"colonnes ......................... {len(art.columns)} : {', '.join(art.columns)}")
    for col in ["product_group_name", "product_type_name", "colour_group_name", "index_group_name", "garment_group_name"]:
        if col in art.columns:
            vc = art[col].value_counts(sort=True).head(8)
            p(f"top {col} :")
            for r in vc.to_dicts(): p(f"   {r[col]} : {r['count']:,}".replace(",", " "))

    section("H&M — customers.csv  (" + fsize(CUSTOMERS) + ")")
    cu = pl.read_csv(CUSTOMERS, infer_schema_length=10000)
    p(f"lignes (clients) ................. {cu.height:,}".replace(",", " "))
    p(f"colonnes ......................... {', '.join(cu.columns)}")
    if "age" in cu.columns:
        a = cu.select(pl.col("age")).drop_nulls()
        p(f"âge .............................. min={a['age'].min()}  médiane={a['age'].median()}  moy={a['age'].mean():.1f}  max={a['age'].max()}  (nuls={cu.height-a.height:,})".replace(",", " "))
    for col in ["club_member_status", "fashion_news_frequency"]:
        if col in cu.columns:
            vc = cu[col].value_counts(sort=True).head(6)
            p(f"{col} :")
            for r in vc.to_dicts(): p(f"   {r[col]} : {r['count']:,}".replace(",", " "))
except Exception as e:
    p("ERREUR H&M :", repr(e))

# ---------------------------------------------------------------- Fashion
try:
    import pandas as pd
    section("FASHION — styles.csv  (" + fsize(STYLES) + ")")
    df = pd.read_csv(STYLES, on_bad_lines="skip", engine="python")
    p(f"lignes (produits) ................ {len(df):,}".replace(",", " "))
    p(f"colonnes ......................... {', '.join(df.columns)}")
    for col in ["gender", "masterCategory", "subCategory", "articleType", "baseColour", "season", "usage"]:
        if col in df.columns:
            vc = df[col].value_counts(dropna=False).head(8)
            p(f"top {col} :")
            for k, v in vc.items(): p(f"   {k} : {int(v):,}".replace(",", " "))
    if "year" in df.columns:
        yrs = pd.to_numeric(df["year"], errors="coerce").dropna()
        if len(yrs): p(f"année ............................ {int(yrs.min())} → {int(yrs.max())}")
    miss = df.isna().sum()
    miss = miss[miss > 0]
    if len(miss):
        p("valeurs manquantes :")
        for k, v in miss.items(): p(f"   {k} : {int(v):,}".replace(",", " "))

    section("FASHION — dossier images/")
    if os.path.isdir(IMAGES):
        n_jpg = sum(1 for f in os.listdir(IMAGES) if f.lower().endswith(".jpg"))
        p(f"images .jpg ...................... {n_jpg:,}".replace(",", " "))
    else:
        p("dossier images/ introuvable :", IMAGES)
except Exception as e:
    p("ERREUR Fashion :", repr(e))

# ---------------------------------------------------------------- écriture
try:
    docs = os.path.join(HOME, "Documents", "miroir", "bloc2-architecture", "docs")
    os.makedirs(docs, exist_ok=True)
    with open(os.path.join(docs, "data_profile.md"), "w") as f:
        f.write("# Miroir — Profil des données (généré)\n\n```\n" + "\n".join(OUT) + "\n```\n")
    p("\n[OK] Rapport écrit dans bloc2-architecture/docs/data_profile.md")
except Exception as e:
    p("\n[!] écriture md échouée :", repr(e))
