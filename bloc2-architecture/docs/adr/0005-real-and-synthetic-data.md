# ADR 0005 — Données réelles + synthétiques

## Statut
Accepte

## Contexte
Aucun dataset public ne contient a la fois des profils de conseil en image et un volume
transactionnel credible.

## Decision
Combiner des datasets reels (Fashion pour le catalogue, H&M pour le volume/signal) avec des
donnees synthetiques generees par regles coherentes (profils clientes, conseilleres, evenements).

## Consequences
- Volume data engineering credible (31M transactions reelles).
- Profils metier coherents (morphotype, palette, style) generes selon des distributions realistes.
- Choix assume et documente face au jury.
