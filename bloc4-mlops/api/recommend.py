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
    candidates = retrieve_fn(anchor_vec, occasion)
    if exclude_ids:
        excl = {str(x) for x in exclude_ids}
        candidates = [c for c in candidates if str(c["item_id"]) not in excl]
    if not candidates:
        return []

    features = feature_fn(profile, candidates, occasion)
    scores = model.predict(features)

    ranked = sorted(zip(candidates, scores), key=lambda x: float(x[1]), reverse=True)[:k]

    return [
        ItemReco(
            item_id=str(c["item_id"]),
            score=float(s),
            article_type=c.get("article_type"),
            base_colour=c.get("base_colour"),
            usage=c.get("usage"),
            image_url=c.get("image_url"),
        )
        for c, s in ranked
    ]
