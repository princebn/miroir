# ADR 0003 — pgvector pour le vector store

## Statut
Accepte

## Contexte
La recherche visuelle (embeddings CLIP) necessite un stockage et une recherche vectorielle.

## Decision
Utiliser l'extension `pgvector` sur PostgreSQL plutot qu'un vector store dedie (Pinecone, Qdrant).

## Consequences
- Une seule base pour le metier ET les vecteurs : moins d'operationnel.
- Jointures directes embeddings <-> metadata produit.
- Index ANN (ivfflat/hnsw) cree au Bloc 4 apres calcul des embeddings.
