# ADR-0007 — Séparation des environnements Python

**Statut** : Accepté

## Contexte
Le projet combine des dépendances aux contraintes incompatibles : Airflow, dbt (qui exige `pathspec<0.13`), black, torch, Evidently.

## Décision
Isoler Airflow dans un environnement virtuel dédié (`.venv-airflow`). L'environnement ML/data (`.venv`) héberge le serving, l'entraînement, Great Expectations et Evidently. Les tâches du DAG invoquent explicitement l'interpréteur Python du venv ML.

## Conséquences
- Élimine les conflits de dépendances entre l'orchestrateur et la stack ML.
- Chaque environnement reste cohérent et reproductible.
- Coût : deux environnements à provisionner, chemins d'interpréteur explicites dans le DAG.

## Alternatives écartées
- **Venv unique** : incompatibilités bloquantes (ex. `pathspec` dbt vs black).
- **Conteneuriser chaque composant** : surcoût injustifié pour une démo locale.
