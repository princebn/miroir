# ADR-0003 — Interactions synthétiques pour l'amorçage

**Statut** : Accepté

## Contexte
Au lancement, aucune donnée d'usage réelle n'existe (démarrage à froid). Il faut néanmoins entraîner le re-ranker et démontrer le pipeline complet.

## Décision
Générer des profils et des interactions synthétiques cohérents, via des règles de compatibilité (morphologie, colorimétrie saisonnière, archétypes), avec un taux d'approbation réaliste (~16 %). Toutes ces données sont tracées comme [SYNTHÉTIQUE].

## Conséquences
- Permet d'industrialiser le pipeline de bout en bout dès le départ.
- Honnêteté méthodologique : les hypothèses sont explicites et traçables.
- Les performances sont à lire comme une preuve d'architecture, non comme une preuve métier.
- Le réentraînement intégrera progressivement le feedback réel collecté via `/feedback`.

## Alternatives écartées
- **Attendre des données réelles** : impossible à l'amorçage.
- **Réutiliser un dataset tiers** : non aligné avec le persona et les attributs métier.
