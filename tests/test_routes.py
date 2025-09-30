import pytest
from app import create_app
import app.routes as routes_module


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


# ---------- /results ----------
def test_results_with_query_and_sorting(monkeypatch, client):
    monkeypatch.setattr(
        routes_module, "search_recipes",
        lambda ingredients: [
            {"id": 1, "name": "Pizza", "ingredients": ["cheese", "tomato"]},
            {"id": 2, "name": "Salad", "ingredients": ["lettuce", "tomato"]},
        ]
    )

    resp = client.get("/results?ingredients=cheese,tomato&sort_by=matches")
    assert resp.status_code == 200
    assert b"Pizza" in resp.data or b"Salad" in resp.data


def test_results_empty_query(client):
    resp = client.get("/results")
    assert resp.status_code == 200
    assert b"No recipes" in resp.data or b"No recipes found" in resp.data


# ---------- /recipe/<id> ----------
def test_recipe_detail_found(monkeypatch, client):
    monkeypatch.setattr(
        routes_module, "get_recipe_details",
        lambda rid: {"id": rid, "name": "Pizza", "ingredients": ["cheese"], "instructions": "Bake"}
    )
    resp = client.get("/recipe/1")
    assert resp.status_code == 200
    assert b"Pizza" in resp.data


def test_recipe_detail_not_found(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_recipe_details", lambda rid: None)
    resp = client.get("/recipe/999")
    assert resp.status_code == 404


# ---------- /my_recipes ----------
def test_my_recipes(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipes", lambda: [{"id": 1, "name": "Soup"}])
    resp = client.get("/my_recipes")
    assert resp.status_code == 200
    assert b"Soup" in resp.data


# ---------- /my_recipes/new ----------
def test_new_recipe_get(client):
    resp = client.get("/my_recipes/new")
    assert resp.status_code == 200
    assert b"form" in resp.data or b"Recipe" in resp.data


def test_new_recipe_post_valid(monkeypatch, client):
    called = {}

    def fake_save(name, ingredients, instructions, source, api_id):
        called["ok"] = True

    monkeypatch.setattr(routes_module, "save_user_recipe", fake_save)

    resp = client.post("/my_recipes/new", data={
        "name": "Test Soup",
        "ingredients": "water,salt",
        "instructions[]": ["Boil water", "Add salt"]
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert "ok" in called


def test_new_recipe_post_invalid(client):
    resp = client.post("/my_recipes/new", data={
        "name": "", "ingredients": "", "instructions[]": []
    }, follow_redirects=True)
    # Redirects anyway, but nothing saved
    assert resp.status_code == 200


# ---------- /my_recipes/<id>/edit ----------
def test_edit_recipe_get(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipe", lambda rid: {
        "id": rid, "name": "Soup", "ingredients": ["water"], "instructions": "Boil", "source": "user"
    })
    resp = client.get("/my_recipes/1/edit")
    assert resp.status_code == 200
    assert b"Soup" in resp.data


def test_edit_recipe_not_found(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipe", lambda rid: None)
    resp = client.get("/my_recipes/999/edit")
    assert resp.status_code == 404


def test_edit_recipe_forbidden(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipe", lambda rid: {"id": rid, "source": "api"})
    resp = client.get("/my_recipes/1/edit")
    assert resp.status_code == 403


def test_edit_recipe_post_valid(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipe", lambda rid: {
        "id": rid, "name": "Soup", "ingredients": ["water"], "instructions": "Boil", "source": "user"
    })
    monkeypatch.setattr(routes_module, "update_user_recipe", lambda *a, **kw: True)

    resp = client.post("/my_recipes/1/edit", data={
        "name": "New Soup",
        "ingredients": "water,salt",
        "instructions[]": ["Boil water", "Add salt"]
    }, follow_redirects=True)

    assert resp.status_code == 200


def test_edit_recipe_post_update_fail(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipe", lambda rid: {
        "id": rid, "name": "Soup", "ingredients": ["water"], "instructions": "Boil", "source": "user"
    })
    monkeypatch.setattr(routes_module, "update_user_recipe", lambda *a, **kw: False)

    resp = client.post("/my_recipes/1/edit", data={
        "name": "Bad Soup",
        "ingredients": "water",
        "instructions[]": ["Just fail"]
    })
    assert resp.status_code == 400


# ---------- /my_recipes/<id>/delete ----------
def test_delete_recipe(monkeypatch, client):
    monkeypatch.setattr(routes_module, "delete_user_recipe", lambda rid: True)
    resp = client.post("/my_recipes/1/delete", follow_redirects=True)
    assert resp.status_code == 200


# ---------- /save_recipe ----------
def test_save_recipe_valid(monkeypatch, client):
    called = {}

    def fake_save(name, ingredients, instructions, source, api_id):
        called["saved"] = (name, ingredients, instructions, source, api_id)

    monkeypatch.setattr(routes_module, "save_user_recipe", fake_save)

    resp = client.post("/save_recipe", data={
        "name": "API Soup",
        "ingredients": "water,salt",
        "instructions": "Boil",
        "api_id": "42"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert "saved" in called
    assert called["saved"][3] == "api"


def test_save_recipe_invalid(client):
    resp = client.post("/save_recipe", data={
        "name": "", "ingredients": "", "instructions": ""
    }, follow_redirects=True)
    assert resp.status_code == 200  


# ---------- /ingredient_suggestions ----------
def test_ingredient_suggestions(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_ingredient_suggestions", lambda q: ["salt", "sugar"])
    resp = client.get("/ingredient_suggestions?query=s")
    assert resp.status_code == 200
    assert b"salt" in resp.data
    assert b"sugar" in resp.data



# ---------- Edge Cases / Cache & Error Handling ----------

def test_recipe_detail_not_found(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_recipe_details", lambda rid: None)
    resp = client.get("/recipe/999")
    assert resp.status_code == 404
    assert b"Recipe not found" in resp.data


def test_edit_recipe_not_found(monkeypatch, client):
    monkeypatch.setattr(routes_module, "get_user_recipe", lambda rid: None)
    resp = client.get("/my_recipes/123/edit")
    assert resp.status_code == 404
    assert b"Recipe not found" in resp.data


def test_edit_recipe_forbidden(monkeypatch, client):
    monkeypatch.setattr(
        routes_module,
        "get_user_recipe",
        lambda rid: {"id": rid, "source": "api", "instructions": "Step 1"}
    )
    resp = client.get("/my_recipes/123/edit")
    assert resp.status_code == 403
    assert b"not allowed" in resp.data.lower()


def test_edit_recipe_update_fails(monkeypatch, client):
    monkeypatch.setattr(
        routes_module,
        "get_user_recipe",
        lambda rid: {"id": rid, "source": "user", "instructions": "Step 1"}
    )
    monkeypatch.setattr(routes_module, "update_user_recipe", lambda *a, **kw: False)

    resp = client.post(
        "/my_recipes/123/edit",
        data={"name": "Test", "ingredients": "cheese", "instructions[]": "Bake"},
    )
    assert resp.status_code == 400
    assert b"Unable to update recipe" in resp.data


def test_results_cache_reuse(monkeypatch, client):
    called = {"count": 0}

    def fake_search(user_ingredients):
        called["count"] += 1
        return [{"id": 1, "name": "Pizza", "ingredients": ["cheese", "tomato"]}]

    monkeypatch.setattr(routes_module, "search_recipes", fake_search)

    routes_module.recipe_cache.clear()

    resp1 = client.get("/results?ingredients=cheese,tomato")
    assert resp1.status_code == 200
    assert called["count"] == 1

    resp2 = client.get("/results?ingredients=cheese,tomato")
    assert resp2.status_code == 200
    assert called["count"] == 1  

