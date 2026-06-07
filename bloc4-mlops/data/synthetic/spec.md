# Spec — Données synthétiques (profils & interactions)

## 1. Pourquoi

Miroir est un projet de mémoire ; aucune donnée client réelle n'existe. On simule des profils et des interactions pour amorcer le développement et l'entraînement du re-ranker. Toutes les décisions de génération sont auditables et reproductibles.

## 2. Périmètre — profils clients

- **Volume** : 50 consultantes × 30 clientes = **1 500 profils**
- **Reproductibilité** : seed fixe `42`, sortie identique à chaque exécution
- **Sortie** : `data/synthetic/profiles.parquet`

Six attributs structurés par profil.

### 2.1 Morphologie

| Valeur | Part |
|--------|------|
| sablier | 35 % |
| rectangle | 25 % |
| triangle | 22 % |
| triangle_inverse | 10 % |
| ovale | 8 % |

Distribution informée par la littérature de mode (typologies courantes en conseil en image).

### 2.2 Saison colorimétrique

12 sous-saisons (système Sci\ART à 12 catégories) :

`printemps_clair, printemps_chaud, printemps_lumineux, ete_doux, ete_froid, ete_lumineux, automne_chaud, automne_profond, automne_doux, hiver_froid, hiver_profond, hiver_lumineux`

Distribution **uniforme** (1/12 chacune).

### 2.3 Archétypes de style

6 archétypes (modèle simplifié inspiré Kibbe) ; chaque cliente en a **1 à 3**.

`classique, naturel, romantique, dramatique, creatif, elegant_chic`

| Nombre d'archétypes | Part |
|---------------------|------|
| 1 | 60 % |
| 2 | 30 % |
| 3 | 10 % |

### 2.4 Budget

| Tranche | Plage € | Part |
|---------|---------|------|
| bas | < 50 | 20 % |
| milieu_bas | 50 – 150 | 45 % |
| milieu_haut | 150 – 400 | 25 % |
| premium | > 400 | 10 % |

L'unité est l'euro **synthétique**.

### 2.5 Occasions

6 occasions ; chaque cliente en a **1 à 3**.

`bureau, cocktail, vacances, sport, soiree, casual`

| Nombre d'occasions | Part |
|--------------------|------|
| 1 | 30 % |
| 2 | 50 % |
| 3 | 20 % |

### 2.6 Taille

| Taille | Part |
|--------|------|
| XS | 8 % |
| S | 25 % |
| M | 38 % |
| L | 22 % |
| XL | 7 % |

### 2.7 Schéma `profiles.parquet`

| Colonne | Type | Description |
|---------|------|-------------|
| client_id | str (uuid4) | Identifiant unique de la cliente |
| consultante_id | str (uuid4) | Consultante qui gère cette cliente |
| morphologie | str (enum) | cf. 2.1 |
| saison_colorimetrique | str (enum) | cf. 2.2 |
| archetypes | list\[str\] | 1-3 valeurs, cf. 2.3 |
| budget_tranche | str (enum) | cf. 2.4 |
| occasions | list\[str\] | 1-3 valeurs, cf. 2.5 |
| taille | str (enum) | cf. 2.6 |

---

## 3. Périmètre — interactions cliente × article

- **Volume** : 1 500 profils × 30 articles = **45 000 interactions**
- **Reproductibilité** : seed `42`
- **Sortie** : `data/synthetic/interactions.parquet`
- **Source articles** : table `catalog.item_embeddings` (Bloc 4 étape 3)

### 3.1 Filtre dur

On échantillonne uniquement parmi les articles dont `gender ∈ {Women, Unisex}`. Cohérent avec la persona Aïcha qui sert une clientèle féminine.

### 3.2 Score combiné

Pour chaque paire (cliente, article, occasion), on calcule trois sous-scores ∈ \[0, 1\], puis un score combiné pondéré :

```
combined = 0,40 × color_score
         + 0,40 × occasion_score
         + 0,20 × archetype_score
```

**Label** = 1 si `combined ≥ 0,70`, sinon 0. Puis on inverse le label avec probabilité **5 %** pour simuler le bruit d'une décision humaine (un humain n'est jamais 100 % cohérent — le modèle doit l'apprendre).

### 3.3 Score couleur

Mapping documenté dans `src/synth/compatibility.py::SAISON_PALETTES`.

Chaque sous-saison définit deux jeux de couleurs :
- **Tier 1 (signature)** : 6 à 10 couleurs piliers de la palette → score **1,0**
- **Tier 2 (compatible)** : 5 à 7 couleurs élargies → score **0,6**
- **Hors palette** → score **0,1**
- **`None`, `Multi`, `Metallic`** → score neutre **0,4**

Référence : système Sci\ART (12 sous-saisons), méthode reconnue en conseil en image.

### 3.4 Score occasion

| Occasion cliente | `usage` article compatibles |
|------------------|----------------------------|
| bureau | Formal, Smart Casual |
| cocktail | Party, Formal, Smart Casual |
| vacances | Casual, Travel, Ethnic |
| sport | Sports |
| soiree | Party, Formal |
| casual | Casual, Smart Casual |

- Match → score **1,0**
- Pas de match → score **0,2**
- `usage = None` → score neutre **0,3**

### 3.5 Score archétype (proxy)

**Mise en garde** : les archétypes de style ne sont pas une métadonnée native du dataset Fashion. On utilise `articleType` comme **proxy** documenté dans `compatibility.py::ARCHETYPE_ARTICLE_TYPES`. Liste extraite par jugement de mode (Shirts → classique ; Dresses → romantique ; Sneakers → naturel ; etc.).

- Si l'`articleType` matche **au moins un** archétype de la cliente → score **1,0**
- Sinon → score de repli **0,4** (un article hors signature n'est pas exclu d'office)

### 3.6 Schéma `interactions.parquet`

| Colonne | Type | Description |
|---------|------|-------------|
| interaction_id | str (uuid4) | Identifiant unique de l'interaction |
| client_id | str | FK vers `profiles.client_id` |
| item_id | str | FK vers `catalog.item_embeddings.item_id` |
| occasion | str | Occasion tirée des occasions de la cliente |
| label | int | 1 = approuvé, 0 = écarté |
| color_score | float | ∈ \[0, 1\], cf. 3.3 |
| occasion_score | float | ∈ \[0, 1\], cf. 3.4 |
| archetype_score | float | ∈ \[0, 1\], cf. 3.5 |
| combined_score | float | ∈ \[0, 1\], cf. 3.2 |

Les 4 colonnes de score sont conservées en sortie : utiles pour le débogage et l'analyse, **non utilisées** comme features d'entraînement (sinon le modèle apprendrait directement la règle).

---

## 4. Limites assumées

- **Stationnaire** : aucune dimension temporelle ; pas de saisonnalité de demande
- **Indépendance** : chaque profil est tiré indépendamment, aucun cluster modélisé par consultante
- **Apprentissage de la règle, pas de la demande** : un modèle entraîné uniquement sur ces données apprendra les règles de génération. La valeur réelle vient du réentraînement sur les **vraies décisions d'Aïcha** en production (boucle MLOps du Bloc 4)
- **Proxy archétype** : `articleType → archétype` est un mapping de jugement, pas une vérité terrain. À remplacer par un signal réel dès qu'il existera
- **Budget** : ignoré dans la génération d'interactions (le catalogue Fashion ne contient pas de prix). Le budget interviendra en filtrage côté API, pas en entraînement
