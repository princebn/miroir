"""Tests for the Miroir recommendation API (orchestrator + endpoints, fully mocked)."""

import numpy as np
from fastapi.testclient import TestClient

from api import recommend as recommend_mod
from api.main import app
from api.schemas import ItemReco


def _fake_anchor(occasion, saison, archetypes):
    return np.zeros(512, dtype=np.float32)


def _fake_retrieve(anchor, occasion, n_candidates=200, gender_allowed=("Women", "Unisex")):
    return [
        {
            "item_id": f"item_{i}",
            "article_type": "Topwear",
            "base_colour": "Blue",
            "usage": "Casual",
            "season": "Spring",
            "image_url": None,
            "cosine_distance": 0.1 + 0.05 * i,
        }
        for i in range(10)
    ]


def _fake_profile(client_id):
    return {
        "client_id": client_id,
        "morphologie": "sablier",
        "saison_colorimetrique": "automne_doux",
        "archetypes": ["classique"],
        "budget_tranche": "milieu_haut",
        "taille": "M",
        "occasions": ["bureau"],
    }


class _FakeModel:
    def predict(self, X):
        return np.linspace(1.0, 0.0, num=len(X))


def _fake_features(profile, candidates, occasion):
    return np.zeros((len(candidates), 10))


def test_recommend_orchestrator_returns_top_k():
    items = recommend_mod.recommend(
        client_id="abc",
        occasion="bureau",
        k=5,
        profile_fn=_fake_profile,
        anchor_fn=_fake_anchor,
        retrieve_fn=_fake_retrieve,
        feature_fn=_fake_features,
        model=_FakeModel(),
    )
    assert len(items) == 5
    assert all(isinstance(it, ItemReco) for it in items)


def test_recommend_orchestrator_sorts_by_score_desc():
    items = recommend_mod.recommend(
        client_id="abc",
        occasion="bureau",
        k=3,
        profile_fn=_fake_profile,
        anchor_fn=_fake_anchor,
        retrieve_fn=_fake_retrieve,
        feature_fn=_fake_features,
        model=_FakeModel(),
    )
    scores = [it.score for it in items]
    assert scores == sorted(scores, reverse=True)


def test_recommend_orchestrator_empty_candidates_returns_empty():
    items = recommend_mod.recommend(
        client_id="abc",
        occasion="bureau",
        k=5,
        profile_fn=_fake_profile,
        anchor_fn=_fake_anchor,
        retrieve_fn=lambda a, o, **kw: [],
        feature_fn=_fake_features,
        model=_FakeModel(),
    )
    assert items == []


def test_health_endpoint_returns_status():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert body["status"] in ("ok", "degraded")


def test_recommend_endpoint_validates_occasion():
    client = TestClient(app)
    r = client.post("/recommend", json={"client_id": "abc", "occasion": "invalid", "k": 5})
    assert r.status_code == 422


def test_recommend_endpoint_validates_k_min():
    client = TestClient(app)
    r = client.post("/recommend", json={"client_id": "abc", "occasion": "bureau", "k": 0})
    assert r.status_code == 422


def test_recommend_endpoint_validates_k_max():
    client = TestClient(app)
    r = client.post("/recommend", json={"client_id": "abc", "occasion": "bureau", "k": 100})
    assert r.status_code == 422


def test_recommend_endpoint_validates_client_id_not_empty():
    client = TestClient(app)
    r = client.post("/recommend", json={"client_id": "", "occasion": "bureau", "k": 5})
    assert r.status_code == 422


def test_feedback_validates_action():
    client = TestClient(app)
    r = client.post(
        "/feedback",
        json={"client_id": "abc", "item_id": "1", "occasion": "bureau", "action": "maybe"},
    )
    assert r.status_code == 422


def test_feedback_validates_occasion():
    client = TestClient(app)
    r = client.post(
        "/feedback",
        json={"client_id": "abc", "item_id": "1", "occasion": "invalide", "action": "approved"},
    )
    assert r.status_code == 422
