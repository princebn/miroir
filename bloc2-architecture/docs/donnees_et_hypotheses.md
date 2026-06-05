# Miroir — Données & hypothèses (fiche de sourcing)

> Référence unique pour TOUT chiffre utilisé dans les livrables Miroir (slides, doc, oral).
> Principe : aucun chiffre n'apparaît dans une slide s'il n'est pas dans cette fiche, avec sa source et son statut.
> Généré le 2026-06-05. Données réelles relevées par `explore_data.py` (voir `data_profile.md`).

**Légende des statuts**
- `[MESURÉ]` — relevé sur les fichiers réels, sur la machine, le 2026-06-05.
- `[DATASET]` — propriété connue du dataset Kaggle source.
- `[CALCULÉ]` — dérivé par calcul direct des comptages mesurés (formule indiquée).
- `[SYNTHÉTIQUE]` — donnée à générer par règles (pas encore produite).
- `[HYPOTHÈSE]` — prémisse du cas Miroir (brief), non sourcée en externe.
- `[MARCHÉ]` — estimation d'un cabinet d'études commercial (à citer comme ordre de grandeur).

---

## 0. Avertissement de périmètre (à dire au jury)

Miroir est un **cas fictif**. Les données « réelles » utilisées sont des **datasets Kaggle publics** servant de **proxy réaliste** (volume, structure, signal de recommandation) — ce ne sont **pas** les données propres de Miroir. Les données clientes/conseillères de Miroir sont **synthétiques**, générées par règles cohérentes. Cette distinction est assumée et défendable : elle permet une volumétrie crédible pour l'ingénierie de données sans inventer de fausses données clientes.

Sources des datasets :
- Fashion Product Images (Param Aggarwal) — Kaggle : https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset
- H&M Personalized Fashion Recommendations — Kaggle competition : https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations

---

## 1. Données réelles mesurées — proxy catalogue + signal

### 1.1 Transactions (signal collaborative filtering) — H&M `transactions_train.csv` (3,49 Go)

| Chiffre | Valeur | Statut |
|---|---|---|
| Transactions | **31 788 324** | `[MESURÉ]` |
| Période | **2018-09-20 → 2020-09-22** (734 jours, ~2 ans) | `[MESURÉ]` |
| Clients distincts | **1 362 281** | `[MESURÉ]` |
| Articles distincts | **104 547** | `[MESURÉ]` |
| Moyenne transactions / jour | **43 308** | `[CALCULÉ]` 31 788 324 ÷ 734 |
| Canal de vente 2 | 22 379 862 (**70,4 %**) | `[MESURÉ]` / `[CALCULÉ]` |
| Canal de vente 1 | 9 408 462 (**29,6 %**) | `[MESURÉ]` / `[CALCULÉ]` |
| Prix | médiane 0,0254 · moyenne 0,0278 · p90 0,0508 (min 0,00002 / max 0,5915) | `[MESURÉ]` |

⚠️ **Prix = unité normalisée du dataset, PAS des euros.** Ne jamais présenter en € ni convertir. À mentionner uniquement comme distribution relative, ou à ne pas afficher.

Saisonnalité (volume mensuel) : oscille entre ~1,0 M et ~1,9 M transactions/mois ; pics en **juin** (juin 2019 : 1 906 202 ; juin 2020 : 1 764 507). Mois de bord partiels : 2018-09 (594 776) et 2020-09 (798 269). `[MESURÉ]`

### 1.2 Catalogue articles — H&M `articles.csv` (36,1 Mo)

| Chiffre | Valeur | Statut |
|---|---|---|
| Articles | **105 542** (25 colonnes) | `[MESURÉ]` |
| Top groupe produit | Garment Upper body 42 741 · Lower body 19 812 · Full body 13 292 | `[MESURÉ]` |
| Top couleur | Black 22 670 · Dark Blue 12 171 · White 9 542 | `[MESURÉ]` |
| Top segment | Ladieswear 39 737 · Baby/Children 34 711 · Menswear 12 553 | `[MESURÉ]` |

### 1.3 Clients — H&M `customers.csv` (207,1 Mo)

| Chiffre | Valeur | Statut |
|---|---|---|
| Clients (table) | **1 371 980** | `[MESURÉ]` |
| Couverture transactionnelle | 1 362 281 / 1 371 980 ont ≥1 achat (**99,3 %**) | `[CALCULÉ]` |
| Âge | médiane **32** · moyenne **36,4** (min 16 / max 99 ; 15 861 nuls) | `[MESURÉ]` |
| Membres club ACTIVE | 1 272 491 (**92,7 %**) | `[MESURÉ]` / `[CALCULÉ]` |

### 1.4 Catalogue produits Miroir + recherche visuelle — Fashion `styles.csv` (4,3 Mo) + `images/`

| Chiffre | Valeur | Statut |
|---|---|---|
| Produits catalogués | **44 424** (10 colonnes) | `[MESURÉ]` |
| Images JPG | **44 441** | `[MESURÉ]` |
| Écart images / catalogue | **+17 images** sans métadonnée (ou lignes ignorées au parsing) | `[CALCULÉ]` |
| Répartition genre | Men 49,9 % · Women 41,9 % · Unisex 4,9 % | `[MESURÉ]` / `[CALCULÉ]` |
| Usage | Casual **77,4 %** · Sports 9,1 % · Ethnic 7,2 % · Formal 5,3 % | `[MESURÉ]` / `[CALCULÉ]` |
| Saison | Summer 48,3 % · Fall 25,7 % · Winter 19,2 % · Spring 6,7 % | `[MESURÉ]` / `[CALCULÉ]` |
| Période catalogue | **2007 → 2019** | `[MESURÉ]` |
| Complétude | très bonne : manquants usage 317, season 21, baseColour 15, year 1 | `[MESURÉ]` |

---

## 2. Données synthétiques (à générer — pas encore produites)

| Élément | Volume cible | Statut | Source |
|---|---|---|---|
| Profils clientes fictives | ~5 000 | `[SYNTHÉTIQUE]` | brief Miroir |
| Conseillères fictives | ~50 (20–100 clientes chacune) | `[SYNTHÉTIQUE]` | brief Miroir |
| Événements (stream) | quelques milliers / jour | `[SYNTHÉTIQUE]` | brief Miroir |

Génération par règles cohérentes (morphotype A/V/H/O/X/8, 12 saisons colorimétriques, sous-ton de peau, archétypes de style, occasions). **Aucun chiffre à présenter comme réel tant que non généré.**

---

## 3. Hypothèses business / persona (brief — NON sourcées en externe)

| Chiffre | Valeur | Statut |
|---|---|---|
| Temps perdu en recherche produit | 60 % | `[HYPOTHÈSE]` brief, persona Aïcha |
| Gain de temps visé | ~10 h / semaine | `[HYPOTHÈSE]` brief |
| Clientes par conseillère | ~30 | `[HYPOTHÈSE]` brief |

**Règle slides** : si affichés, ces chiffres portent la mention « hypothèse du cas ». Aucune source externe ne les valide. Alternative recommandée : les remplacer par un repère marché sourcé (§4) ou par un fait mesuré (§1).

---

## 4. Repères marché externes (ordres de grandeur — sources commerciales)

⚠️ Estimations de cabinets d'études (market research), non revues par les pairs, à **forte dispersion** entre fournisseurs. À citer comme ordres de grandeur, jamais comme chiffres exacts. **Chaque ligne ci-dessous a été vérifiée à la source le 2026-06-05** (voir note d'audit en fin de section).

### 4.1 Repères principaux (vérifiés à la source, les + pertinents pour Miroir)

| Repère | Valeur (vérifiée) | Source |
|---|---|---|
| **AI-driven personal styling** (le + proche du positionnement IA de Miroir) | **1,8 Md$ (2025) → 9,7 Md$ (2034), CAGR 20,4 %** (2026-2034) ; régions : Amérique du Nord 38,2 %, **Europe 27,4 %**, Asie-Pacifique 22,6 % ; logiciel 62,5 % du marché | DataIntelo — dataintelo.com/report/ai-driven-personal-styling-market (maj mars 2026) |
| → opportunité **B2B AI styling tools** (segment de Miroir) | estimée **> 800 M$ d'ici 2030** ; financement VC AI fashion-tech **> 1,2 Md$** cumulé 2024-2025 | idem (même rapport) |
| **Personal shopping service** | **3,8 Md$ (2024) → 11,2 Md$ (2033), CAGR 12,7 %** | MarketIntelo — marketintelo.com/report/personal-shopping-service-market |

### 4.2 Repères secondaires (contexte conseil en image — forte dispersion)

| Repère | Valeur | Source |
|---|---|---|
| Conseil en image mondial | ~4,5 Md$ (2025), CAGR ~7,2 % → 2032 | Coherent Market Insights — coherentmarketinsights.com/market-insight/image-consulting-market-6106 |
| (estimation divergente) | ~9,3 Md$ (2023), CAGR ~5,8 % | Verified Market Reports — verifiedmarketreports.com/product/image-consulting-service-market/ |
| Luxury personal styling | ~2,65 Md$ (2024), CAGR ~8,7 % → 2033 | DataIntelo — dataintelo.com/report/luxury-personal-styling-market |
| France — profession conseil en image | enquête métier 2021 (profil, tarifs, CA) — **payante, non acquise** | AFIPP — helloasso.com/associations/afipp/boutiques/etude-de-marche-enquete-metier-conseil-en-image-v-juin-2021 |

Aucun chiffre AFIPP n'est repris : l'étude n'a pas été acquise.

### 4.3 Note d'audit (écarts relevés à la vérification)

- Le rapport **AI-driven personal styling** a été annoncé en interne à « $1,82 Bn 2024, CAGR 21,7 %, Europe 20,5 % ». La page DataIntelo (maj mars 2026) indique en réalité **1,8 Md$ en 2025, CAGR 20,4 %, Europe 27,4 %**. → on retient les valeurs **de la page**, pas les valeurs annoncées.
- L'URL **ai-personal-stylist-market** redirige vers **le même rapport** que ai-driven-personal-styling-market : ce n'est **pas une source distincte**. Les chiffres « Asie 24,7 % / 320 M$ GenAI 2024 » ne sont pas confirmés sur la page (qui mentionne Asie-Pacifique CAGR 23,7 % et VC > 1,2 Md$ cumulé 2024-2025).
- **Personal shopping service** : annoncé « 3,8 Md$ 2024, CAGR 12,7 % » → **confirmé** à la source.

---

## 5. TAM / SAM / SOM Miroir

Cadrage marché. **Seul le TAM est dérivé d'une source ; SAM et SOM sont des hypothèses cadrées, à défendre, pas des faits.** Math explicite à chaque ligne.

| Niveau | Valeur | Construction | Statut |
|---|---|---|---|
| **TAM** — AI-driven personal styling, **Europe** | **≈ 0,49 Md$ (2025)**, croissance ~19,2 %/an | 1,8 Md$ (marché mondial 2025) × 27,4 % (part Europe) = 0,493 Md$ | `[CALCULÉ]` depuis DataIntelo |
| **SAM** — outils **B2B SaaS pour conseillères pro** (Europe) | **≈ 50–60 M$** (hypothèse) | ~10–15 % du TAM Europe adressable en B2B pour praticiennes indépendantes (≠ apps B2C, ≠ e-commerce). Point d'appui : le rapport chiffre l'opportunité B2B AI styling tools > 800 M$ mondial d'ici 2030 | `[HYPOTHÈSE]` cadrée — à affiner |
| **SOM** — ambition Miroir **à 3 ans** | **≈ 0,5 M€ ARR** | ~300 conseillères abonnées × ~1 800 €/an (≈ 150 €/mois) ≈ 540 k€/an | `[HYPOTHÈSE]` cadrée |

**Inputs à firmer (sinon attaquables en Q&R) :**
- Part B2B du SAM : choix assumé 10–15 %, aucune source directe → à argumenter (le rapport ne ventile pas « tooling praticiennes indépendantes »).
- Nombre de conseillères cibles + prix d'abonnement : hypothèses. Le **nombre de conseillères en Europe** se firme via l'**enquête AFIPP** (§4.2) ou un recensement NAF/registre pro.
- Conversion USD/EUR non appliquée au TAM (laissé en USD) ; au taux ~1,08, TAM Europe ≈ 0,46 Md€.

---

## 6. Liste verte — chiffres défendables pour les slides Bloc 2

Les seuls chiffres à utiliser dans les slides, chacun directement traçable ci-dessus :

- **31,8 M** transactions réelles (H&M) · `[MESURÉ]`
- **2 ans** d'historique, **43 308** transactions/jour en moyenne · `[MESURÉ/CALCULÉ]`
- **1,36 M** clients distincts · **104 547** articles · `[MESURÉ]`
- **44 424** produits catalogués + **44 441** images · `[MESURÉ]`
- Catalogue **2007–2019**, complétude élevée · `[MESURÉ]`
- **70 %** des ventes sur un seul canal · `[CALCULÉ]`
- Repère marché principal : AI-driven personal styling **CAGR 20,4 %/an**, **Europe 27,4 %** du marché · `[MARCHÉ]` (DataIntelo, vérifié) — ⚠️ **20,4 %, pas 21,7 %**
- TAM Europe **≈ 0,49 Md$ (2025)** · `[CALCULÉ]` ; SAM/SOM = `[HYPOTHÈSE]` à étiqueter

Tout le reste (60 %, 10 h, 30 clientes) = `[HYPOTHÈSE]` à étiqueter ou retirer.
