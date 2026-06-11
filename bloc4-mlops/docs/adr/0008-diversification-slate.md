# ADR-0008 — Diversification du slate de recommandation

**Statut** : Accepté

## Contexte
Le re-ranker maximise la pertinence pièce par pièce : le top-k brut peut se
concentrer sur un seul type d'article (ex. cinq jupes), alors que le livrable
métier est une sélection variée permettant de composer une proposition.

## Décision
Diversification post-classement dans l'orchestrateur : au plus `max_per_type`
pièces par `article_type` (2 au serving), complétées par les meilleurs scores
restants si nécessaire. Paramètre optionnel, désactivé par défaut — le
comportement historique de `recommend()` est inchangé sans l'option.

## Conséquences
- La sélection servie est composable (types variés), sans toucher au modèle.
- Technique standard de diversité de slate, peu coûteuse et explicable au jury.
- Le plafond (2) est un paramètre métier à calibrer.
- Couvert par des tests unitaires dédiés (`tests/test_diversification.py`).

## Alternatives écartées
- **MMR sur embeddings** : plus coûteux et opaque pour un bénéfice équivalent ici.
- **Contrainte de catégorie en SQL (retrieval)** : rigide, mélange les étages.
