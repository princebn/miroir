#!/usr/bin/env python3
"""Miroir Bloc 3 - Console d'intelligence de la demande (interactive)."""
import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

ENGINE = create_engine("postgresql+psycopg2://miroir:miroir_local_pwd@localhost:5432/miroir")
st.set_page_config(page_title="Miroir - Console demande", page_icon="M", layout="wide")

CREME, OR, ENCRE, SABLE, GRIS = "#FAF6EE", "#B8956A", "#1A1410", "#F0E9DC", "#6B5D4F"
MUTED = "#D8C7A8"
CMAP = {
    "Black": "#222222", "White": "#D8D2C4", "Off White": "#CFC8B8",
    "Dark Blue": "#27324B", "Blue": "#3B6FB0", "Light Blue": "#9CBFDD",
    "Grey": "#9A9389", "Dark Grey": "#555049", "Light Grey": "#BDB6A8",
    "Light Pink": "#EBB9C6", "Pink": "#E392A8", "Light Beige": "#D9C7A6",
    "Beige": "#C9B393", "Red": "#B23A33", "Green": "#4E7A52", "Dark Green": "#33503A",
    "Brown": "#6F4E37", "Yellow": "#E2B33B", "Orange": "#D98A40",
    "Turquoise": "#4FB0A5", "Purple": "#6E5A86", "Khaki green": "#6E6B42",
    "Other": OR, "Inconnu": MUTED, "Mole": "#8C7A5E", "Yellowish Green": "#A9B45A",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Outfit:wght@300;400;500;600&display=swap');
#MainMenu, header, footer {{visibility:hidden;}}
.stApp {{background:{CREME};}}
.block-container {{padding-top:2.2rem; padding-bottom:3rem; max-width:1240px;}}
html,body,[class*="css"],.stMarkdown,p,span,div {{font-family:'Outfit',sans-serif; color:{ENCRE};}}
h1,h2,h3 {{font-family:'Fraunces',serif !important; color:{ENCRE};}}
.m-title {{font-family:'Fraunces',serif; font-size:2.4rem; font-weight:600; line-height:1.05; margin:0;}}
.m-sub {{color:{GRIS}; font-size:.98rem; margin:.35rem 0 1.1rem; font-weight:300;}}
.flow {{display:flex; align-items:center; flex-wrap:wrap; gap:.4rem; margin-bottom:1rem;}}
.chip {{background:{SABLE}; border:1px solid {OR}; color:{ENCRE}; padding:.26rem .66rem; border-radius:999px; font-size:.76rem; font-weight:500;}}
.arr {{color:{OR}; font-weight:600;}}
.band {{font-family:'Fraunces',serif; font-size:.82rem; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:{OR}; margin:1.8rem 0 .2rem;}}
.band-sub {{color:{GRIS}; font-size:.82rem; font-weight:300; margin-bottom:.8rem;}}
.kpi-row {{display:flex; gap:.8rem; flex-wrap:wrap; margin:.4rem 0 .4rem;}}
.kpi {{flex:1; min-width:150px; background:#fff; border:1px solid {SABLE}; border-left:3px solid {OR}; border-radius:10px; padding:.85rem 1rem;}}
.kpi-label {{color:{GRIS}; font-size:.72rem; font-weight:500; text-transform:uppercase; letter-spacing:.05em;}}
.kpi-value {{font-family:'Fraunces',serif; font-size:1.55rem; font-weight:600; margin-top:.2rem; line-height:1;}}
.kpi-value.sm {{font-size:1.05rem;}}
.sec {{font-family:'Fraunces',serif; font-size:1.16rem; font-weight:600; margin:.2rem 0 .15rem;}}
.take {{background:{SABLE}; border-left:3px solid {OR}; border-radius:0 8px 8px 0; padding:.5rem .8rem; font-size:.9rem; margin:.2rem 0 .7rem;}}
.take b {{color:{ENCRE};}}
.lede {{background:#fff; border:1px solid {SABLE}; border-radius:12px; padding:1rem 1.15rem; font-size:1.02rem; line-height:1.5; margin:.3rem 0 1rem;}}
</style>
""", unsafe_allow_html=True)

def fr(n):
    try: return f"{int(n):,}".replace(",", " ")
    except Exception: return str(n)

def frM(n):
    n = float(n)
    if n >= 1_000_000: return f"{n/1_000_000:.2f} M".replace(".", ",")
    if n >= 1_000: return f"{n/1_000:.0f} k"
    return fr(n)

@st.cache_data(ttl=60)
def q(sql):
    return pd.read_sql(sql, ENGINE)

def take(html):
    st.markdown(f'<div class="take">{html}</div>', unsafe_allow_html=True)

AX = dict(grid=False, labelColor=ENCRE, domainColor="#D8CDBB", labelLimit=220)

def hbar(df, dim, val, n=8):
    d = df.head(n)
    return (alt.Chart(d).mark_bar(color=OR, cornerRadiusEnd=3).encode(
            x=alt.X(f"{val}:Q", title=None, axis=alt.Axis(format="~s")),
            y=alt.Y(f"{dim}:N", title=None, sort="-x"),
            tooltip=[alt.Tooltip(f"{dim}:N", title=dim.capitalize()),
                     alt.Tooltip(f"{val}:Q", title="Transactions", format=",")])
            .properties(height=250).configure_view(strokeWidth=0)
            .configure_axis(**AX).configure_axisX(labelColor=GRIS))

# ===== EN-TETE =====
st.markdown('<div class="m-title">Miroir &mdash; Console de demande temps réel</div>'
            '<div class="m-sub">Pipeline streaming H&amp;M industrialisé. Ces signaux alimentent le moteur de recommandation de Miroir (Bloc 4).</div>',
            unsafe_allow_html=True)
st.markdown('<div class="flow">'
    '<span class="chip">Kafka</span><span class="arr">&rarr;</span>'
    '<span class="chip">Postgres</span><span class="arr">&rarr;</span>'
    '<span class="chip">dbt</span><span class="arr">&rarr;</span>'
    '<span class="chip">Great Expectations</span><span class="arr">&rarr;</span>'
    '<span class="chip">Airflow</span><span class="arr">&rarr;</span>'
    '<span class="chip">Streamlit</span></div>', unsafe_allow_html=True)

# ===== FLUX TEMPS REEL =====
st.markdown('<div class="band">Flux temps réel &mdash; monitoring du pipeline</div>', unsafe_allow_html=True)
try:
    s = q("SELECT count(*) n, count(distinct customer_id) c, count(distinct article_id) a, "
          "min(t_dat) dmin, max(t_dat) dmax, max(loaded_at) last FROM signals.stream_transactions").iloc[0]
    per = f"{s.dmin} &rarr; {s.dmax}" if s.dmin is not None else "&mdash;"
    st.markdown('<div class="kpi-row">'
        f'<div class="kpi"><div class="kpi-label">Transactions streamées</div><div class="kpi-value">{fr(s.n)}</div></div>'
        f'<div class="kpi"><div class="kpi-label">Clients (flux)</div><div class="kpi-value">{fr(s.c)}</div></div>'
        f'<div class="kpi"><div class="kpi-label">Articles (flux)</div><div class="kpi-value">{fr(s.a)}</div></div>'
        f'<div class="kpi"><div class="kpi-label">Période échantillonnée</div><div class="kpi-value sm">{per}</div></div>'
        f'<div class="kpi"><div class="kpi-label">Dernier chargement</div><div class="kpi-value sm">{str(s.last)[:16] if s.last is not None else "&mdash;"}</div></div>'
        '</div>', unsafe_allow_html=True)
    st.caption("Flux validé par dbt (not_null, domaine canal) + Great Expectations (6 attentes) ; le DAG Airflow échoue si la qualité échoue.")
except Exception as e:
    st.error(f"Flux indisponible : {e}")

# ===== INTELLIGENCE DE LA DEMANDE =====
st.markdown('<div class="band">Intelligence de la demande &mdash; 31,8 M transactions réelles</div>'
            '<div class="band-sub">Agrégats dbt sur 2 ans, enrichis par la taxonomie produit et la démographie. Filtre interactif ci-dessous.</div>',
            unsafe_allow_html=True)
try:
    tot = q("SELECT n_transactions, distinct_customers, distinct_articles FROM analytics.mart_totals").iloc[0]
    seg = q("SELECT segment, n_transactions, distinct_customers, distinct_articles FROM analytics.mart_segment ORDER BY n_transactions DESC")
    segcat = q("SELECT segment, categorie, n_transactions FROM analytics.mart_seg_category")
    segcol = q("SELECT segment, couleur, n_transactions FROM analytics.mart_seg_colour")
    segage = q("SELECT segment, tranche_age, n_transactions FROM analytics.mart_seg_age")
    segmon = q("SELECT segment, mois, n_transactions FROM analytics.mart_seg_month")

    seg_list = seg["segment"].tolist()
    sel = st.selectbox("Filtrer par segment", ["Tous les segments"] + seg_list, index=0)
    is_all = sel.startswith("Tous")

    if is_all:
        ktx, kcli, kart = tot.n_transactions, tot.distinct_customers, tot.distinct_articles
        klabel = "Clients distincts"
    else:
        r = seg[seg["segment"] == sel].iloc[0]
        ktx, kcli, kart = r.n_transactions, r.distinct_customers, r.distinct_articles
        klabel = "Clients acheteurs"
    st.markdown('<div class="kpi-row">'
        f'<div class="kpi"><div class="kpi-label">Transactions</div><div class="kpi-value">{frM(ktx)}</div></div>'
        f'<div class="kpi"><div class="kpi-label">{klabel}</div><div class="kpi-value">{frM(kcli)}</div></div>'
        f'<div class="kpi"><div class="kpi-label">Articles distincts</div><div class="kpi-value">{frM(kart)}</div></div>'
        f'<div class="kpi"><div class="kpi-label">Part du volume</div><div class="kpi-value">{("100" if is_all else f"{ktx/tot.n_transactions*100:.0f}")} %</div></div>'
        '</div>', unsafe_allow_html=True)

    # ---------- HEATMAP D'AFFINITE (flagship) ----------
    st.markdown('<div class="sec">Affinité segment × catégorie — sur/sous-indexation vs le marché</div>', unsafe_allow_html=True)
    grand = segcat["n_transactions"].sum()
    seg_tot = segcat.groupby("segment")["n_transactions"].sum()
    cat_tot = segcat.groupby("categorie")["n_transactions"].sum()
    top_segs = seg_tot.sort_values(ascending=False).head(8).index.tolist()
    top_cats = cat_tot.sort_values(ascending=False).head(8).index.tolist()
    h = segcat[segcat["segment"].isin(top_segs) & segcat["categorie"].isin(top_cats)].copy()
    h["index"] = (h["n_transactions"] / h["segment"].map(seg_tot)) / (h["categorie"].map(cat_tot) / grand)
    hmax = h.loc[h["index"].idxmax()]
    take(f'Lecture : un indice &gt; 1 = le segment <b>sur-consomme</b> la catégorie vs la moyenne. '
         f'Plus fort signal : <b>{hmax.segment}</b> sur <b>{hmax.categorie}</b> '
         f'(indice <b>{hmax["index"]:.1f}×</b>) — opportunité de recommandation ciblée.')
    base = alt.Chart(h)
    rect = base.mark_rect().encode(
        x=alt.X("categorie:N", title=None, sort=top_cats, axis=alt.Axis(labelAngle=-30, labelLimit=160)),
        y=alt.Y("segment:N", title=None, sort=top_segs),
        color=alt.Color("index:Q", title="Indice",
                        scale=alt.Scale(domain=[0, 1, 2, 3], range=["#F2EDE1", "#E2D2B4", OR, ENCRE], clamp=True),
                        legend=alt.Legend(orient="right")),
        tooltip=[alt.Tooltip("segment:N"), alt.Tooltip("categorie:N"),
                 alt.Tooltip("index:Q", title="Indice", format=".2f"),
                 alt.Tooltip("n_transactions:Q", title="Transactions", format=",")])
    txt = base.mark_text(fontSize=11).encode(
        x=alt.X("categorie:N", sort=top_cats), y=alt.Y("segment:N", sort=top_segs),
        text=alt.Text("index:Q", format=".1f"),
        color=alt.condition(alt.datum.index > 1.8, alt.value("white"), alt.value(ENCRE)))
    heat = ((rect + txt).properties(height=330).configure_view(strokeWidth=0)
            .configure_axis(grid=False, labelColor=ENCRE, domainColor="#D8CDBB")
            .configure_legend(labelColor=ENCRE, titleColor=GRIS))
    st.altair_chart(heat, use_container_width=True)

    # ---------- panneaux pilotes par le filtre ----------
    def by(df, dim):
        d = df if is_all else df[df["segment"] == sel]
        return d.groupby(dim, as_index=False)["n_transactions"].sum().sort_values("n_transactions", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Mix par segment client</div>', unsafe_allow_html=True)
        sg = seg.copy()
        sg["hl"] = OR if is_all else sg["segment"].map(lambda x: ENCRE if x == sel else MUTED)
        top = seg.iloc[0]
        take(f'<b>{top.segment}</b> concentre <b>{top.n_transactions/tot.n_transactions*100:.0f}%</b> du volume.'
             + ("" if is_all else f' Sélection : <b>{sel}</b>.'))
        mix = (alt.Chart(sg.head(8)).mark_bar(cornerRadiusEnd=3).encode(
               x=alt.X("n_transactions:Q", title=None, axis=alt.Axis(format="~s")),
               y=alt.Y("segment:N", title=None, sort="-x"),
               color=alt.Color("hl:N", scale=None, legend=None),
               tooltip=[alt.Tooltip("segment:N"), alt.Tooltip("n_transactions:Q", format=",")])
               .properties(height=250).configure_view(strokeWidth=0)
               .configure_axis(**AX).configure_axisX(labelColor=GRIS))
        st.altair_chart(mix, use_container_width=True)
    with c2:
        st.markdown('<div class="sec">Demande par catégorie</div>', unsafe_allow_html=True)
        cat = by(segcat, "categorie")
        tc = cat.iloc[0]
        take(f'<b>{tc.categorie}</b> en tête (<b>{tc.n_transactions/cat["n_transactions"].sum()*100:.0f}%</b>).')
        st.altair_chart(hbar(cat, "categorie", "n_transactions"), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="sec">Démographie acheteurs</div>', unsafe_allow_html=True)
        order = ["16-24", "25-34", "35-44", "45-54", "55+", "Inconnu"]
        ag = by(segage, "tranche_age")
        ag["o"] = ag["tranche_age"].map({v: i for i, v in enumerate(order)}).fillna(99)
        ag = ag.sort_values("o")
        kn = ag[ag["tranche_age"] != "Inconnu"]
        if len(kn):
            tb = kn.sort_values("n_transactions", ascending=False).iloc[0]
            take(f'Cœur de cible : <b>{tb.tranche_age} ans</b> (<b>{tb.n_transactions/ag["n_transactions"].sum()*100:.0f}%</b>).')
        bar = (alt.Chart(ag).mark_bar(color=OR, cornerRadiusEnd=3).encode(
               x=alt.X("tranche_age:N", title=None, sort=order),
               y=alt.Y("n_transactions:Q", title=None, axis=alt.Axis(format="~s")),
               tooltip=[alt.Tooltip("tranche_age:N", title="Âge"), alt.Tooltip("n_transactions:Q", format=",")])
               .properties(height=250).configure_view(strokeWidth=0)
               .configure_axis(**AX).configure_axisY(labelColor=GRIS))
        st.altair_chart(bar, use_container_width=True)
    with c4:
        st.markdown('<div class="sec">Palette la plus achetée</div>', unsafe_allow_html=True)
        co = by(segcol, "couleur").head(8)
        co["hex"] = co["couleur"].map(CMAP).fillna(MUTED)
        take(f'<b>{co.iloc[0].couleur}</b> en tête — entrée directe pour les palettes Miroir.')
        cbar = (alt.Chart(co).mark_bar(cornerRadiusEnd=3, stroke="#C9BCA0", strokeWidth=.7).encode(
                x=alt.X("n_transactions:Q", title=None, axis=alt.Axis(format="~s")),
                y=alt.Y("couleur:N", title=None, sort="-x"),
                color=alt.Color("hex:N", scale=None, legend=None),
                tooltip=[alt.Tooltip("couleur:N"), alt.Tooltip("n_transactions:Q", format=",")])
                .properties(height=250).configure_view(strokeWidth=0)
                .configure_axis(**AX).configure_axisX(labelColor=GRIS))
        st.altair_chart(cbar, use_container_width=True)

    # ---------- saisonnalite ----------
    st.markdown('<div class="sec">Saisonnalité de la demande</div>', unsafe_allow_html=True)
    sm = segmon.copy()
    sm["mois"] = pd.to_datetime(sm["mois"])
    if is_all:
        top5 = seg.head(5)["segment"].tolist()
        sm["seg"] = sm["segment"].where(sm["segment"].isin(top5), "Autres")
        sm = sm.groupby(["mois", "seg"], as_index=False)["n_transactions"].sum()
        peak = sm.groupby("mois")["n_transactions"].sum().idxmax()
        take(f'Pic de demande : <b>{peak.strftime("%B %Y")}</b>. La saisonnalité conditionne le bon moment de recommandation.')
        dom = top5 + ["Autres"]
        rng = [ENCRE, OR, "#8C7A5E", "#C9B48E", "#6B5D4F", "#D8CDBB"][:len(dom)]
        area = (alt.Chart(sm).mark_area(opacity=0.92).encode(
                x=alt.X("mois:T", title=None),
                y=alt.Y("n_transactions:Q", title="Transactions / mois", stack=True, axis=alt.Axis(format="~s")),
                color=alt.Color("seg:N", scale=alt.Scale(domain=dom, range=rng), legend=alt.Legend(title=None, orient="top")),
                tooltip=[alt.Tooltip("mois:T", title="Mois"), alt.Tooltip("seg:N", title="Segment"),
                         alt.Tooltip("n_transactions:Q", format=",")]))
    else:
        sm = sm[sm["segment"] == sel].groupby("mois", as_index=False)["n_transactions"].sum()
        peak = sm.set_index("mois")["n_transactions"].idxmax()
        take(f'Segment <b>{sel}</b> — pic : <b>{peak.strftime("%B %Y")}</b>.')
        area = (alt.Chart(sm).mark_area(opacity=0.9, color=OR, line={"color": ENCRE}).encode(
                x=alt.X("mois:T", title=None),
                y=alt.Y("n_transactions:Q", title="Transactions / mois", axis=alt.Axis(format="~s")),
                tooltip=[alt.Tooltip("mois:T", title="Mois"), alt.Tooltip("n_transactions:Q", format=",")]))
    area = (area.properties(height=300).configure_view(strokeWidth=0)
            .configure_axis(grid=False, labelColor=GRIS, titleColor=GRIS, domainColor="#D8CDBB")
            .configure_legend(labelColor=ENCRE))
    st.altair_chart(area, use_container_width=True)

    st.caption("Prix H&M = unité normalisée du dataset, jamais des euros. "
               "Dataset sans géolocalisation (postal_code anonymisé) : aucune carte n'est inventée.")
except Exception as e:
    st.error(f"Intelligence de la demande indisponible : {e}")
    st.info("Lance d'abord : dbt build --select tag:reference")

if st.button("Rafraîchir"):
    st.cache_data.clear()
    st.rerun()
