# tests/test_routes.py
import pytest
from app import create_app
import app.routes as routes_module

def make_client():
    app = create_app()
    app.testing = True
    return app.test_client()

def test_results_stores_session(monkeypatch):
    # fake API: returns two simple recipes
    def fake_search(user_ingredients):
        return [
            {"id": 1, "name": "Pizza", "ingredients": ["cheese", "tomato"]},
            {"id": 2, "name": "Salad", "ingredients": ["lettuce", "tomato"]},
        ]
    # patch the function used by routes.py
    monkeypatch.setattr(routes_module, "search_recipes", fake_search)

    client = make_client()
    resp = client.get("/results?ingredients=cheese,tomato&sort_by=matches")
    assert resp.status_code == 200

    # confirm session got populated with last_results, last_ingredients, last_sort
    with client.session_transaction() as sess:
        assert "last_results" in sess
        assert "last_ingredients" in sess
        assert "last_sort" in sess

        last = sess["last_results"]
        assert isinstance(last, list)
        # find the Pizza recipe and verify augmentation
        pizza = next((r for r in last if r.get("id") == 1), None)
        assert pizza is not None
        assert pizza["name"] == "Pizza"
        assert "matches" in pizza and isinstance(pizza["matches"], list)
        assert "missing_count" in pizza
        # both ingredients match -> matches length 2, missing_count 0
        assert len(pizza["matches"]) == 2
        assert pizza["missing_count"] == 0

def test_back_to_results_uses_session(monkeypatch):
    # patch search_recipes and get_recipe_details
    monkeypatch.setattr(
        routes_module,
        "search_recipes",
        lambda user_ingredients: [{"id": 1, "name": "Pizza", "ingredients": ["cheese", "tomato"]}],
    )
    monkeypatch.setattr(
        routes_module,
        "get_recipe_details",
        lambda rid: {"id": rid, "name": "Pizza", "ingredients": ["cheese", "tomato"], "instructions": "Bake"},
    )

    client = make_client()
    # 1) do the search (this should write the session)
    r1 = client.get("/results?ingredients=cheese,tomato&sort_by=weighted")
    assert r1.status_code == 200

    # 2) visit the recipe detail (simulates user clicking a recipe)
    r2 = client.get("/recipe/1")
    assert r2.status_code == 200

    # 3) now "back to results" -> call /results with NO params
    r3 = client.get("/results")
    assert r3.status_code == 200

    # The page returned should contain the recipe name stored in session
    assert b"Pizza" in r3.data

def test_no_session_and_no_params_shows_empty_state():
    # If there's no session and no query params, /results should still return OK
    # and show the "no results" / empty state (check for 'No recipes' substring).
    client = make_client()
    resp = client.get("/results")
    assert resp.status_code == 200
    assert b"No recipes" in resp.data or b"No recipes found" in resp.data

