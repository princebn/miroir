# ADR-0002 — LightGBM pour le re-ranker

**Statut** : Accepté

## Contexte
Le re-ranking porte sur des features tabulaires structurées (one-hot morphologie/colorimétrie/archétypes, ordinaux budget/taille, occasion, attributs produit). Les données d'entraînement sont limitées (synthétiques), et l'on vise interprétabilité et latence faible sur CPU (serving conteneurisé).

## Décision
Gradient boosting **LightGBM** (LGBMClassifier). Quatre configurations comparées, sélection sur l'AUC de validation, gestion du déséquilibre via `scale_pos_weight`.

## Conséquences
- Excellent sur données tabulaires en faible volume.
- Inférence rapide sur CPU, compatible avec le conteneur de serving.
- Feature importance directement exploitable.
- Pas d'apprentissage de représentations — compensé par les embeddings CLIP en amont.

## Alternatives écartées
- **Réseau de neurones** : sur-paramétré pour ce volume, opaque, latence plus élevée.
- **Régression logistique** : sous-capacitaire pour les interactions non linéaires entre attributs.
