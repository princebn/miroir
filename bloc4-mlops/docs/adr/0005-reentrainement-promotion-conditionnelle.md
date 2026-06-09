# ADR-0005 — Réentraînement à promotion conditionnelle et rollback

**Statut** : Accepté

## Contexte
Un réentraînement périodique automatique ne doit jamais dégrader la production de façon silencieuse.

## Décision
DAG Airflow hebdomadaire : régénération des données → garde-fou qualité (Great Expectations, bloquant) → entraînement → évaluation challenger vs champion sur le jeu de test. L'alias `production` n'est promu que si `AUC_challenger ≥ AUC_champion − 0,005` ; sinon rollback (le champion est conservé).

## Conséquences
- Protection contre les régressions de performance.
- Qualité des données vérifiée avant tout entraînement.
- Décision de promotion/rollback tracée et reproductible.
- La tolérance (0,005) est un paramètre à calibrer.
- Une dérive non captée par le jeu de test échapperait à ce garde-fou — couverte par le monitoring de drift (voir ADR-0006).

## Alternatives écartées
- **Promotion automatique systématique** : risque de régression silencieuse en production.
- **Promotion manuelle** : non scalable, annule le bénéfice de l'automatisation.
