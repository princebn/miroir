# ADR 0002 — Approche ELT (vs ETL)

## Statut
Accepte

## Contexte
Les donnees H&M (31M transactions) doivent etre ingerees puis exploitees.

## Decision
Charger d'abord le brut dans une landing zone (`signals`), puis transformer/nettoyer
en aval (Bloc 3, dbt + Great Expectations).

## Consequences
- Tracabilite et rejouabilite : on re-transforme sans re-telecharger 3,2 Go.
- Separation claire raw / clean.
- Ingestion rapide via `COPY` (pas de transformation couteuse au chargement).
