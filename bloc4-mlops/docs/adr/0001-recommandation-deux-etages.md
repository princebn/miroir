# ADR-0001 — Architecture de recommandation en deux étages

**Statut** : Accepté

## Contexte
Le catalogue compte 44 419 articles. Il faut produire, pour chaque couple (cliente, occasion), des recommandations pertinentes en moins de 300 ms, interprétables pour la conseillère comme pour le jury.

## Décision
Pipeline en deux étages :
1. **Retrieval** — embeddings CLIP (ViT-B-32) du catalogue indexés dans Postgres/pgvector (HNSW, cosinus) ; rappel d'un large ensemble de candidats par proximité visuelle et colorimétrique.
2. **Re-ranking** — modèle LightGBM sur 37 features (attributs cliente + produit + occasion) qui ordonne les candidats et renvoie le top-k.

## Conséquences
- Scalable : le retrieval HNSW est sublinéaire ; le re-ranking ne s'applique qu'aux candidats.
- Interprétable : l'importance des features du re-ranker est exploitable en soutenance et en production.
- Modulaire : chaque étage évolue indépendamment.
- Coût : deux composants à maintenir ; la cohérence des features entre étages doit être garantie.

## Alternatives écartées
- **Modèle end-to-end unique (deep)** : coûteux à entraîner, opaque, médiocre en démarrage à froid, latence supérieure.
