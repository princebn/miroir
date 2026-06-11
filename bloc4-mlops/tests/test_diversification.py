"""Tests de la diversification du slate (max pieces par type d'article)."""

from api.recommend import recommend


class _FakeModel:
    def __init__(self, scores):
        self._scores = scores

    def predict(self, _features):
        return self._scores


def _candidats(types):
    return [
        {
            "item_id": str(i),
            "article_type": t,
            "base_colour": "noir",
            "usage": "Formal",
            "image_url": "",
        }
        for i, t in enumerate(types)
    ]


def _run(types, scores, **kwargs):
    return recommend(
        "client-test",
        "cocktail",
        5,
        profile_fn=lambda _cid: {},
        anchor_fn=lambda *_a: None,
        retrieve_fn=lambda *_a, **_k: _candidats(types),
        feature_fn=lambda *_a: None,
        model=_FakeModel(scores),
        **kwargs,
    )


def test_diversification_plafonne_par_type():
    types = ["Skirts"] * 4 + ["Tops", "Heels", "Handbags", "Jackets"]
    scores = [0.9, 0.89, 0.88, 0.87, 0.5, 0.4, 0.3, 0.2]
    res = _run(types, scores, max_per_type=2)
    assert [r.article_type for r in res].count("Skirts") == 2
    assert len(res) == 5


def test_diversification_complete_au_score_si_types_insuffisants():
    types = ["Skirts"] * 6
    scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    res = _run(types, scores, max_per_type=2)
    assert len(res) == 5
    assert [r.item_id for r in res] == ["0", "1", "2", "3", "4"]


def test_sans_option_comportement_historique():
    types = ["Skirts"] * 4 + ["Tops"]
    scores = [0.9, 0.8, 0.7, 0.6, 0.5]
    res = _run(types, scores)
    assert [r.article_type for r in res].count("Skirts") == 4
