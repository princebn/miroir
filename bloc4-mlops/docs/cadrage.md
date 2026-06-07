# Bloc 4 — Cadrage : Miroir Reco
**Cahier des charges, architecture cible, boucles MLOps**

Document de cadrage du Bloc 4 (Solutions d'Intelligence Artificielle) du mémoire RNCP Data Engineering / MLOps. Ce document fige les choix avant l'implémentation. Toute déviation pendant l'exécution est consignée comme ADR dans `bloc4-mlops/docs/adr/`.

---

## 1. Contexte & enjeu métier

Miroir est une plateforme B2B SaaS fictive à destination des consultants en image indépendants. La cliente-type, **Aïcha**, gère ~30 clientes premium en Europe et Afrique. Sa douleur principale : le temps passé à parcourir des catalogues produits pour identifier, pour chaque cliente, les pièces compatibles avec sa morphologie, sa saison colorimétrique, ses archétypes de style, son budget et l'occasion ciblée.

Le Bloc 4 industrialise un **moteur de recommandation hybride** qui ingère le profil d'une cliente et un contexte (occasion, budget) et retourne une short-list ordonnée d'articles candidats. Aïcha valide ou écarte ; ses décisions enrichissent la boucle de réentraînement.

> Tagline projet : *Miroir industrialise le conseil en image pour révéler le style de chaque cliente, à grande échelle.*

---

## 2. Persona & cas d'usage cible

**Aïcha** — consultante en image, 30 clientes actives, ~5 sélections par cliente et par mois. Utilise Miroir comme outil de pré-tri en amont des shootings et des sessions de personal shopping.

**User story principale :**
> *En tant que* consultante en image, *je veux* qu'à partir du profil d'une cliente et d'une occasion donnée (cocktail, bureau, vacances…), Miroir me propose une short-list de 20 pièces compatibles ordonnées par pertinence, *afin de* réduire de plusieurs heures à quelques minutes le temps de sélection.

**Volumes ciblés (état projet) :**
- ~44 k articles dans le catalogue (Fashion Product Images dataset) **[MESURÉ]**
- ~30 clientes par consultante × ~50 consultantes simulées = ~1 500 profils synthétiques
- ~50 k interactions synthétiques pour l'entraînement (5 sélections / cliente / mois × 12 mois)
- Latence cible API : **p95 < 300 ms** pour un top-20 (cible UX d'un outil interactif)

---

## 3. Objectifs fonctionnels

| Code | Fonctionnalité | Critère d'acceptation |
|------|---------------|----------------------|
| F1 | Embedding visuel du catalogue | 44 k articles indexés en pgvector, dimension 512 |
| F2 | Profil cliente structuré | 6 dimensions : morphologie, saison colorimétrique, archétypes, budget, occasions, taille |
| F3 | Endpoint `/recommend` | Retourne top-N (paramétrable, défaut 20) par profil + contexte |
| F4 | Re-ranking métier | Score = composite(visuel, colorimétrique, budget, occasion) |
| F5 | Feedback loop | Endpoint `/feedback` capture approuvé / écarté, persisté en base |
| F6 | Réentraînement programmé | DAG Airflow hebdomadaire entraîne le re-ranker sur le delta de feedback |
| F7 | Suivi MLflow | Toute exécution d'entraînement loggue paramètres, métriques (Recall@20, NDCG@20), artefacts |
| F8 | Monitoring drift | Evidently AI compare la distribution des features d'entrée (profils & contextes) entre la fenêtre de référence et la fenêtre courante |

---

## 4. Contraintes non-fonctionnelles

| Aspect | Contrainte |
|--------|-----------|
| **Latence** | p95 < 300 ms sur `/recommend` top-20, p99 < 800 ms |
| **Disponibilité** | Single-AZ en local (Docker Desktop) ; cible cloud = ready pour HA |
| **Reproductibilité** | Tout entraînement traçable (commit SHA + données + hyperparamètres → un run MLflow) |
| **Stack** | Réutiliser autant que possible Bloc 2 et Bloc 3 — pas de duplication d'infra |
| **Versionnage modèle** | Modèles dans MLflow Registry, alias `Production` / `Staging` |
| **Sécurité / RGPD** | Profils clients pseudonymisés (identifiant opaque, pas de PII) — détails dans Bloc 1 |
| **Coût** | 0 € cloud — tout en local Docker Desktop + venv ; cibles cloud documentées mais non déployées |

---

## 5. Données d'entrée

### 5.1 Catalogue produit — réel
**Source** : Kaggle Fashion Product Images Small (paritcl/fashion-product-images-small).
**Volumes mesurés** : 44 424 articles avec image + métadonnées (productDisplayName, gender, masterCategory, subCategory, articleType, baseColour, season, usage). **[MESURÉ]**

### 5.2 Profils clientes — synthétiques
Aucune donnée client réelle n'existe (Miroir est un projet de mémoire). On génère :
- **Morphologie** : 1 parmi {sablier, rectangle, triangle, triangle inversé, ovale} — distribution réaliste documentée dans `bloc4-mlops/data/synthetic/spec.md`
- **Saison colorimétrique** : 1 parmi {printemps clair, été doux, automne profond, hiver froid…} (12 catégories Itten)
- **Archétypes de style** : 1-3 parmi {classique, naturel, romantique, dramatique, créatif, élégant chic}
- **Budget** : tranche {< 50, 50-150, 150-400, > 400} (unité = euros, **synthétique**)
- **Occasions** : 1-3 parmi {bureau, cocktail, vacances, sport, soirée, casual}
- **Taille** : 1 parmi {XS, S, M, L, XL}

### 5.3 Interactions synthétiques
Pour amorcer le re-ranker, on génère ~50 k interactions cliente×article étiquetées `approuvé` ou `écarté` selon des règles d'experte (compatibilité couleur, compatibilité catégorie/occasion, compatibilité budget). Ces règles sont documentées et auditables.

**Limite honnête** : un modèle entraîné sur des interactions synthétiques n'apprend que la règle de génération. Le réentraînement en production sur les vraies décisions d'Aïcha est la vraie boucle de valeur — la phase courante valide le pipeline de bout en bout, pas la performance prédictive absolue.

### 5.4 Signaux H&M (réutilisation Bloc 3)
Les marts segment du Bloc 3 (`mart_seg_category`, `mart_seg_colour`, `mart_seg_age`) fournissent une **distribution marché de référence**. La heatmap d'affinité du Bloc 3 sert de signal de cold-start pour les nouvelles consultantes (proxy de popularité par segment d'âge).

---

## 6. Solution ML proposée

### 6.1 Architecture : retrieval + re-ranking en deux étapes

C'est l'architecture standard des moteurs de reco modernes (YouTube, Spotify, Pinterest) : un premier étage rapide récupère ~200 candidats, un second étage plus fin les ordonne.

```
profil cliente + contexte
        │
        ▼
[ Retrieval ]  pgvector cosine sur embeddings CLIP
        │
        ▼  top-200 candidats
[ Re-ranker ]  LightGBM scoring(candidate, profile, context)
        │
        ▼  top-20 ordonnés
   API /recommend
```

### 6.2 Embeddings produit — CLIP (frozen)

- Modèle : **OpenAI CLIP ViT-B/32** (préentraîné, gelé). Choix défendable : CLIP a appris la sémantique visuelle sur 400 M paires image-texte, donc capture style, matière, couleur sans entraînement supplémentaire.
- Dimension : 512.
- Stockage : `catalog.item_embeddings` (pgvector), index ivfflat ou hnsw.
- Recalcul : déclenché par ajout/maj catalogue (event ou cron) — pas par changement modèle (CLIP reste figé sur le projet).

### 6.3 Re-ranker — LightGBM

- **Modèle** : `LGBMRanker` (objective `lambdarank`).
- **Features** :
  - `cosine_similarity` : score visuel candidat vs profile.style_anchor
  - `color_match` : distance Lab entre saison colorimétrique cliente et couleur dominante article
  - `budget_match` : booléen prix dans la tranche cliente
  - `occasion_match` : Jaccard entre occasions cliente et tags article
  - `category_diversity` : pénalité contre la sur-représentation d'une catégorie déjà sélectionnée
  - `popularity_segment` : signal H&M (Bloc 3) — index d'affinité du segment d'âge de la cliente sur la catégorie de l'article
- **Cible** : binaire `approuvé` (1) ou `écarté` (0).
- **Métriques** : Recall@20, NDCG@20, MAP — toutes calculées sur holdout synthétique.

### 6.4 Profil cliente — encodage

Pas de modèle dédié pour le profil : encodage feature-engineering classique (one-hot, multi-hot, ordinaux). Le re-ranker LightGBM gère nativement ces types.

### 6.5 Pourquoi ces choix

| Décision | Raison |
|---------|--------|
| CLIP gelé, pas fine-tuné | Sans données labellisées massives, fine-tuner CLIP introduit du bruit. Frozen = stable, défendable, économique. |
| 2 étages retrieval + rerank | Pattern industriel éprouvé. Retrieval rapide (vector index), rerank précis (gradient boosting). |
| LightGBM (pas Deep) | Volumes modestes (50 k interactions), features explicables. CatBoost ou XGBoost auraient aussi convenu — LightGBM choisi pour vitesse d'inférence. |
| pgvector (pas Faiss / Pinecone) | Réutilisation Postgres du Bloc 2. Une seule source de vérité, pas de service externe à opérer. |
| Re-ranker explicable | Les features pondérées sont auditables — Aïcha peut comprendre pourquoi tel article remonte. Conformité avec l'esprit RGPD. |

---

## 7. Architecture cible

```
┌────────────────────────────────────────────────────────────────┐
│ INGESTION                                                       │
│  catalogue Kaggle → /raw → preprocess → /processed              │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ EMBEDDINGS                                                      │
│  CLIP ViT-B/32 (frozen) → vectors(512) → pgvector               │
│  catalog.item_embeddings (index ivfflat)                        │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ TRAINING (MLflow tracking)                                      │
│  X = features(client, item, context) ;  y = approuvé/écarté     │
│  LGBMRanker → MLflow run → Registry (Staging → Production)      │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ SERVING (FastAPI)                                               │
│  POST /recommend  → retrieval pgvector + rerank LightGBM        │
│  POST /feedback   → append signals.feedback                     │
│  GET  /metrics    → Prometheus                                  │
└────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│ CI/CD                    │   │ MONITORING                    │
│  GitHub Actions :        │   │  Evidently : feature drift     │
│   lint → test → build →  │   │  Prometheus + Grafana :        │
│   push image → deploy    │   │   latence, QPS, code retour    │
└──────────────────────────┘   └──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ RETRAINING (Airflow)                                            │
│  DAG hebdo : extract feedback → retrain → MLflow → promote      │
│  Promotion automatique si Recall@20 ≥ baseline                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 8. Boucles MLOps

### 8.1 CI/CD

**Pipeline GitHub Actions** (`.github/workflows/bloc4-ci.yml`) déclenché à chaque PR sur `bloc4-mlops/**` :

1. **Lint** — ruff + black sur Python
2. **Unit tests** — pytest sur `tests/` (couvre preprocessing, scoring, API contracts)
3. **Build** — Docker image `miroir-reco-api:${{ github.sha }}`
4. **Push** — GitHub Container Registry (ghcr.io)
5. **Deploy local** — `docker compose up -d` sur le runner (manuel pour production)

Pas de déploiement automatique vers le cloud — assumé hors périmètre. Manifestes K8s prêts pour démonstration.

### 8.2 Réentraînement

**DAG Airflow** `miroir_reco_retrain` (hebdomadaire, cron `0 3 * * 1`) :

1. `extract_feedback` — lit `signals.feedback` depuis la dernière exécution
2. `validate_data` — Great Expectations sur les nouvelles interactions (volume min, distribution des labels)
3. `train` — entraîne LightGBM, log dans MLflow
4. `evaluate` — compare métriques au modèle Production courant sur holdout fixe
5. `promote` — si Recall@20 ≥ baseline-1%, alias `Staging` → `Production` ; sinon échec et alerte

### 8.3 Monitoring

- **Evidently AI** :
  - rapport hebdo `feature_drift_report.html` comparant fenêtre 7j vs baseline 30j
  - features surveillées : distribution morphologie, saison colorimétrique, budget, occasions
  - seuil d'alerte : PSI > 0,2 sur ≥ 2 features
- **Prometheus** (réutilisation Bloc 2) :
  - histogramme latence `/recommend`
  - compteur QPS et code retour
- **Grafana** : dashboard `Bloc 4 — Serving` avec p50/p95/p99, taux d'erreur, drift status

---

## 9. Périmètre & hors périmètre

### Dans le périmètre Bloc 4
- Embeddings CLIP pgvector 44 k articles
- Génération données synthétiques (profils + interactions) avec spec documentée
- Re-ranker LightGBM entraîné + tracké MLflow
- API FastAPI 3 endpoints
- CI/CD GitHub Actions
- DAG réentraînement Airflow
- Monitoring Evidently + Prometheus
- README + ADR + tests unitaires

### Hors périmètre
- Fine-tuning CLIP (frozen)
- Déploiement cloud actif (manifestes K8s livrés, non `kubectl apply`-és en prod)
- Authentification utilisateurs / RBAC (cf. Bloc 1)
- Anonymisation et politique de rétention détaillée (cf. Bloc 1)
- Interface front (Miroir est livré comme API ; un front Streamlit minimal est livré comme démonstrateur uniquement)
- A/B testing en production (la promotion automatique sur Recall@20 tient lieu de validation)

---

## 10. Critères d'acceptation

| # | Critère | Vérification |
|---|---------|-------------|
| C1 | 44 k articles indexés dans pgvector | `SELECT COUNT(*) FROM catalog.item_embeddings` |
| C2 | Recall@20 sur holdout ≥ 0,30 | Run MLflow `eval` |
| C3 | API `/recommend` p95 < 300 ms sur top-20 | Test charge `locust` ou `wrk` |
| C4 | Tests unitaires couverture ≥ 70 % | `pytest --cov` |
| C5 | CI GitHub Actions verte sur main | Badge dans README |
| C6 | DAG réentraînement passe en bout en bout | `airflow dags test miroir_reco_retrain` |
| C7 | Rapport Evidently généré, accessible | `bloc4-mlops/monitoring/reports/latest.html` |
| C8 | README ADR pour 5+ décisions structurantes | `bloc4-mlops/docs/adr/` |

---

## 11. Risques identifiés & mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|-----------|
| Téléchargement CLIP volumineux échoue | Faible | Moyen | Mise en cache locale du modèle, fallback torchvision |
| Embedding 44 k articles trop lent CPU | Moyenne | Moyen | Batch sur GPU si dispo (M4 MPS), sinon échantillon 10 k pour démo |
| Synthèse de données biaisée → reco non défendable | Élevée | Élevé | Documenter explicitement la spec, et insister sur la **boucle réelle** comme valeur cible |
| Modèle synthétique sur-performant en holdout (data leak) | Moyenne | Moyen | Holdout par cliente (split groupé), pas par interaction |
| Latence pgvector + LightGBM > 300 ms | Moyenne | Moyen | Index hnsw au lieu d'ivfflat, top-K retrieval réduit (100 vs 200) |
| Drift Evidently inexploitable car données synthétiques stationnaires | Élevée | Faible | Honnêteté : présenter le rapport comme **plomberie validée**, drift réel constatable seulement en prod |

---

## 12. Plan d'exécution proposé

| Étape | Livrables | Effort estimé |
|-------|-----------|--------------|
| 1. Setup repo `bloc4-mlops/` | structure dossiers, requirements, README initial | court |
| 2. Génération données synthétiques | spec, scripts, holdout | court |
| 3. Embeddings CLIP + ingestion pgvector | script `embed_catalog.py`, table, index | moyen |
| 4. Entraînement re-ranker + MLflow | script `train.py`, runs, métriques | moyen |
| 5. API FastAPI | `/recommend`, `/feedback`, `/metrics`, Dockerfile | moyen |
| 6. CI/CD GitHub Actions | workflow complet, badge README | court |
| 7. DAG réentraînement | DAG, validation, promotion conditionnelle | moyen |
| 8. Monitoring Evidently + Grafana | rapport drift, dashboard | court |
| 9. Slides + démo + ADR | 15-20 slides, script Loom, ADR consolidés | moyen |

---

**Statut document** : version 1, en attente de validation pour démarrage de l'implémentation.
**Prochaine étape** : création de la structure `bloc4-mlops/` et génération des données synthétiques.
