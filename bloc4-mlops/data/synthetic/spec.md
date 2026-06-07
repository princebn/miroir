# Spec — Données synthétiques (profils clients)

## 1. Pourquoi

Miroir est un projet de mémoire ; aucune donnée client réelle n'existe. On simule des profils pour amorcer le développement et l'entraînement du re-ranker. Toutes les décisions de génération sont auditables et reproductibles.

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

Distribution informée par la littérature de mode (typologies courantes en conseil en image). Aucune valeur n'est anecdotique — toutes sont représentées.

### 2.2 Saison colorimétrique

12 sous-saisons (système Sci\ART à 12 catégories) :

`printemps_clair, printemps_chaud, printemps_lumineux, ete_doux, ete_froid, ete_lumineux, automne_chaud, automne_profond, automne_doux, hiver_froid, hiver_profond, hiver_lumineux`

Distribution **uniforme** (1/12 chacune) — aucune raison documentée de privilégier une saison sur l'ensemble d'une population.

### 2.3 Archétypes de style

6 archétypes (modèle simplifié inspiré Kibbe) ; chaque cliente en a **1 à 3**.

`classique, naturel, romantique, dramatique, creatif, elegant_chic`

Distribution du nombre d'archétypes par cliente :

| Nombre d'archétypes | Part |
|---------------------|------|
| 1 | 60 % |
| 2 | 30 % |
| 3 | 10 % |

Hypothèse : la majorité des personnes ont une signature de style dominante.

### 2.4 Budget (tranche)

| Tranche | Plage € | Part |
|---------|---------|------|
| bas | < 50 | 20 % |
| milieu_bas | 50 – 150 | 45 % |
| milieu_haut | 150 – 400 | 25 % |
| premium | > 400 | 10 % |

L'unité est l'euro **synthétique** — pas issue d'un benchmark marché précis.

### 2.5 Occasions

6 occasions ; chaque cliente en a **1 à 3**.

`bureau, cocktail, vacances, sport, soiree, casual`

Distribution du nombre d'occasions par cliente :

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

Distribution informée par les tailles modales européennes femme adulte.

## 3. Schéma de sortie (parquet)

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

## 4. À venir (étape ultérieure)

Les **interactions synthétiques** (paires cliente × article étiquetées approuvé / écarté) seront générées une fois les embeddings CLIP du catalogue calculés. Les règles d'étiquetage combineront compatibilité couleur (saison vs baseColour), catégorie vs occasion, similarité visuelle, et bruit contrôlé. Une spec dédiée sera ajoutée à ce répertoire à ce moment-là.

## 5. Limites assumées

- **Stationnaire** : aucune dimension temporelle, pas de saisonnalité dans la génération
- **Indépendance** : chaque profil est tiré indépendamment ; aucun cluster par consultante n'est modélisé
- **Apprentissage de la règle, pas de la demande** : un modèle entraîné uniquement sur ces données apprendra les règles de génération. La valeur réelle vient de l'enrichissement par les vraies décisions d'Aïcha (boucle de réentraînement en production)
