# ADR 0001 — Modèle B2B SaaS (vs B2C)

## Statut
Accepte

## Contexte
Miroir peut cibler les conseilleres en image (B2B) ou directement les clientes finales (B2C).

## Decision
Cibler les conseilleres independantes (B2B). La conseillere cree les profils, valide et
ajuste les recommandations avant partage.

## Consequences
- RGPD plus defendable : la conseillere agit comme data controller delegue.
- Human-in-the-loop natif : pas de decision automatisee opaque sur la cliente finale.
- Marche de niche identifie, scope ML maitrisable.
