"""Endpoint tests for GET /api/fixtures/{fixture_id}.

These hit the configured DB (like the other endpoint tests). They assert the
route contract that does not depend on seeded data: an unknown id returns 404,
and the literal sibling routes are not shadowed by the int path param.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unknown_fixture_returns_404():
    resp = client.get("/api/fixtures/999999999")
    assert resp.status_code == 404


def test_upcoming_route_not_shadowed_by_fixture_id():
    # /{fixture_id} is an int path param registered after /upcoming; the literal
    # must still resolve (and never be parsed as a fixture id → 422/404).
    resp = client.get("/api/fixtures/upcoming")
    assert resp.status_code == 200
    body = resp.json()
    assert "days" in body and "up_next" in body


def test_live_route_not_shadowed():
    resp = client.get("/api/fixtures/live")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_knockout_route_not_shadowed():
    resp = client.get("/api/fixtures/knockout")
    assert resp.status_code == 200
    assert "rounds" in resp.json()
