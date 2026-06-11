"""Orchestrator: profile -> anchor -> retrieve -> features -> rerank -> top-K."""

from __future__ import annotations

from typing import List

from api.schemas import ItemReco


def recommend(
    client_id: str,
    occasion: str,
    k: int,
    *,
    exclude_ids=None,
    max_per_type=None,
    max_per_colour=None,
    categories=None,
    profile_fn,
    anchor_fn,
    retrieve_fn,
    feature_fn,
    model,
) -> List[ItemReco]:
    profile = profile_fn(client_id)
    saison = profile.get("saison_colorimetrique", "automne_doux")
    archetypes = profile.get("archetypes_style") or []
    if isinstance(archetypes, str):
        archetypes = [archetypes]

    anchor_vec = anchor_fn(occasion, saison, archetypes)
    if categories:
        candidates = retrieve_fn(anchor_vec, occasion, categories=categories)
    else:
        candidates = retrieve_fn(anchor_vec, occasion)
    if exclude_ids:
        excl = {str(x) for x in exclude_ids}
        candidates = [c for c in candidates if str(c["item_id"]) not in excl]
    if not candidates:
        return []

    features = feature_fn(profile, candidates, occasion)
    scores = model.predict(features)

    ranked = sorted(zip(candidates, scores), key=lambda x: float(x[1]), reverse=True)

    if max_per_type or max_per_colour:
        # Diversification du slate : plafonds par type d'article et par
        # couleur, completes par les meilleurs scores restants.
        selected = []
        overflow = []
        type_counts = {}
        colour_counts = {}
        for pair in ranked:
            t = str(pair[0].get("article_type") or "").lower()
            c = str(pair[0].get("base_colour") or "").lower()
            type_ok = not max_per_type or type_counts.get(t, 0) < max_per_type
            colour_ok = not max_per_colour or colour_counts.get(c, 0) < max_per_colour
            if type_ok and colour_ok:
                selected.append(pair)
                type_counts[t] = type_counts.get(t, 0) + 1
                colour_counts[c] = colour_counts.get(c, 0) + 1
            else:
                overflow.append(pair)
            if len(selected) >= k:
                break
        if len(selected) < k:
            selected.extend(overflow[: k - len(selected)])
        ranked = selected
    else:
        ranked = ranked[:k]

    return [
        ItemReco(
            item_id=str(c["item_id"]),
            score=float(s),
            article_type=c.get("article_type"),
            base_colour=c.get("base_colour"),
            usage=c.get("usage"),
            image_url=c.get("image_url"),
            product_display_name=c.get("product_display_name"),
        )
        for c, s in ranked
    ]
