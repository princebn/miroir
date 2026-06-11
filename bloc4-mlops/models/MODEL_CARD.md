# Model Card — miroir_reranker

## Modèle
- Type : LightGBM (LGBMClassifier), re-ranker du pipeline de recommandation à deux étages.
- Version servie : alias `@production` du MLflow Model Registry (v2 à date).
- Entrées : 37 features croisant profil cliente (morphologie, saison colorimétrique, archétypes, budget, taille) × attributs article × occasion.
- Sortie : probabilité d'approbation, utilisée comme clé de classement (le rang est exposé, pas le score brut — scores non calibrés).

## Usage prévu
Ordonner des pièces candidates (issues du retrieval pgvector) pour des clientes
du persona Miroir, sur six occasions (bureau, cocktail, vacances, sport,
soirée, casual). Le modèle propose, la conseillère décide : human-in-the-loop
obligatoire, le système n'envoie rien sans validation humaine.

## Données d'entraînement
- Interactions synthétiques [SYNTHÉTIQUE] générées par règles de compatibilité
  (morphologie, colorimétrie saisonnière, archétypes), taux d'approbation ~16 %.
- 1 500 profils clientes synthétiques ; catalogue Fashion Product Images
  (44 419 articles) [DATASET].
- Aucune donnée personnelle réelle.

## Métriques (jeu de test) [MESURÉ]
- AUC 0,876 · Average Precision 0,80 · NDCG@5 0,42 · Recall@5 0,56.

## Limites connues
- Clientèle féminine uniquement (hors distribution pour les hommes).
- Pas de compatibilité inter-pièces (score par pièce, pas par silhouette).
- Profondeur de personnalisation de niveau amorçage : la finesse viendra du
  feedback réel collecté via `/feedback`.
- Scores saturés sur les données synthétiques : afficher le rang, pas le score.

## Considérations éthiques et conformité
- Les attributs traités (morphologie, colorimétrie) sont des données
  personnelles sensibles : base légale, minimisation et droits des personnes
  relèvent de la politique de gouvernance (Bloc 1).
- Biais possibles hérités du catalogue source ; supervision humaine
  systématique.

## Réentraînement
Hebdomadaire (Airflow) : garde-fou qualité Great Expectations, évaluation
challenger vs champion, promotion seulement si AUC ≥ champion − 0,005, sinon
rollback (ADR-0005). Dérive surveillée par Evidently (ADR-0006).
