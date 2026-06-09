# ADR-0006 — Monitoring de drift à double critère

**Statut** : Accepté

## Contexte
La pertinence du modèle dépend de la stabilité de la distribution des features. Un seuil global unique peut masquer une dérive concentrée sur une feature clé.

## Décision
Rapport Evidently (référence = jeu d'entraînement, courant = échantillon récent). Alerte si le *share* de colonnes en dérive dépasse un seuil (0,2) **OU** si une feature sentinelle (`budget_ord`, `taille_ord`) franchit son seuil de distance de Jensen-Shannon.

## Conséquences
- Sensible aux dérives globales comme aux dérives localisées.
- Les features sentinelles encodent une priorité métier explicite.
- La liste des sentinelles doit rester alignée avec les features du modèle.

## Alternatives écartées
- **Seuil de *share* unique** : aveugle aux dérives concentrées sur peu de colonnes.
- **Surveiller toutes les colonnes sans hiérarchie** : bruyant et peu actionnable.
