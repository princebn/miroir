# ADR-0004 — Serving du modèle via l'alias MLflow `production`

**Statut** : Accepté

## Contexte
Le modèle évolue à chaque réentraînement. Il faut pouvoir changer la version servie sans redéployer l'API.

## Décision
L'API charge `models:/miroir_reranker@production` (avec repli sur la v1 si l'alias est absent). Promouvoir une version revient à déplacer l'alias `production` dans le MLflow Model Registry.

## Conséquences
- Découplage entre le code et la version servie.
- Promotion et rollback instantanés (simple déplacement d'alias), pris en compte au prochain rechargement.
- Traçabilité des versions et de leur lignage.
- Dépendance : le registry MLflow doit être disponible au chargement.

## Alternatives écartées
- **Version figée en dur dans le code** : chaque promotion imposerait un commit et un redéploiement.
- **Chargement d'un `.pkl` local** : aucun versionnement ni lignage.
