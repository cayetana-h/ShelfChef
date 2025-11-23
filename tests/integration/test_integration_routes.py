"""
Integration tests for routes.py
Tests complete HTTP request/response flow through Flask routes
"""
import pytest
from app import create_app
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app = create_app(testing=True)
    return app.test_client()


# ------- tests home routes -----
def test_home_page(client):

    response = client.get("/")
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data


# ------- tests results route -----
@patch("app.routes.get_processed_recipes")
def test_results_with_ingredients(mock_process, client):
    """testing results page shows recipes when ingredients provided"""
    mock_process.return_value = [
        {
            "name": "Pasta",
            "id": 1,
            "matches": ["tomato", "cheese"],
            "missing_count": 0,
            "image": "pasta.jpg"
        }
    ]
    response = client.get("/results?ingredients=tomato,cheese&sort_by=weighted")
    assert response.status_code == 200
    assert b"Pasta" in response.data
    assert b"tomato" in response.data

def test_results_without_ingredients(client):
    """testing results page shows no recipes when no ingredients provided"""
    response = client.get("/results")
    assert response.status_code == 200
    assert b"No recipes found" in response.data


# ------- tests recipe detail route -----
@patch("app.routes.fetch_recipe_or_404")
def test_recipe_detail_success(mock_fetch, client):
    """testing that recipe detail page shows recipe info"""
    mock_fetch.return_value = {
        "name": "Spaghetti",
        "instructions": "Boil pasta and add sauce",
        "ingredients": ["pasta", "tomato sauce"],
        "image": "spaghetti.jpg",
        "sourceUrl": "http://example.com"
    }
    response = client.get("/recipe/123")
    assert response.status_code == 200
    assert b"Spaghetti" in response.data
    assert b"Boil pasta" in response.data

@patch("app.routes.fetch_recipe_or_404")
def test_recipe_detail_not_found(mock_fetch, client):
    mock_fetch.side_effect = ValueError("Recipe not found")
    response = client.get("/recipe/999")
    assert response.status_code == 404


# ------- tests my recipes route -----
@patch("app.routes.RecipeStorage.get_user_recipes")
def test_my_recipes_list(mock_get, client):
    """testing that my recipes page lists user recipes"""
    mock_get.return_value = [
        {"id": 1, "name": "Salad", "source": "user"},
        {"id": 2, "name": "Soup", "source": "api"}
    ]
    response = client.get("/my_recipes")
    assert response.status_code == 200
    assert b"Salad" in response.data
    assert b"Soup" in response.data

def test_new_recipe_form_get(client):
    response = client.get("/my_recipes/new")
    assert response.status_code == 200

@patch("app.routes.RecipeStorage.save_user_recipe")
@patch("app.routes.process_new_recipe_form")
def test_new_recipe_post_success(mock_process, mock_save, client):
    """testing that new recipe form submission saves recipe and redirects"""
    mock_process.return_value = (True, "", ["flour", "water"], "Mix and bake")
    
    response = client.post("/my_recipes/new", data={
        "name": "Bread",
        "ingredients": "flour\nwater",
        "instructions": "Mix and bake"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    mock_save.assert_called_once()
    assert b"My Recipes" in response.data

@patch("app.routes.process_new_recipe_form")
def test_new_recipe_post_validation_error(mock_process, client):
    mock_process.return_value = (False, "Name is required", None, None)
    response = client.post("/my_recipes/new", data={
        "name": "",
        "ingredients": "flour",
        "instructions": "Bake"
    })
    
    assert response.status_code == 200
    assert b"New Recipe" in response.data or b"Recipe Form" in response.data


# ------- tests edit recipe route -----
@patch("app.routes.RecipeStorage.get_user_recipe")
def test_edit_recipe_form_get(mock_get, client):
    """testing that edit recipe form renders with existing data"""
    mock_get.return_value = {
        "id": 1,
        "name": "Pasta",
        "ingredients": "pasta\nsauce",
        "instructions": "Cook pasta",
        "source": "user"
    }
    response = client.get("/my_recipes/1/edit")
    assert response.status_code == 200
    assert b"Pasta" in response.data

@patch("app.routes.RecipeStorage.get_user_recipe")
def test_edit_recipe_not_found(mock_get, client):
    mock_get.return_value = None
    response = client.get("/my_recipes/999/edit")
    assert response.status_code == 404

@patch("app.routes.RecipeStorage.get_user_recipe")
def test_edit_api_recipe_forbidden(mock_get, client):
    """testing that editing an API-sourced recipe is forbidden"""
    mock_get.return_value = {"id": 1, "source": "api"}
    response = client.get("/my_recipes/1/edit")
    assert response.status_code == 403
    assert b"not allowed" in response.data

@patch("app.routes.RecipeStorage.update_user_recipe")
@patch("app.routes.RecipeStorage.get_user_recipe")
@patch("app.routes.process_new_recipe_form")
def test_edit_recipe_post_success(mock_process, mock_get, mock_update, client):
    mock_get.return_value = {"id": 1, "source": "user"}
    mock_process.return_value = (True, "", ["pasta", "sauce"], "Cook it")
    mock_update.return_value = True
    
    response = client.post("/my_recipes/1/edit", data={
        "name": "Updated Pasta",
        "ingredients": "pasta\nsauce",
        "instructions": "Cook it"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    mock_update.assert_called_once()


# ------- tests edit recipe route -----
@patch("app.routes.RecipeStorage.delete_user_recipe")
def test_delete_recipe(mock_delete, client):
    """testing that deleting recipe redirects to my recipes"""
    response = client.post("/my_recipes/1/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_delete.assert_called_once_with(1)


# ------- tests save api recipe route -----
@patch("app.routes.RecipeStorage.save_user_recipe")
@patch("app.routes.extract_api_recipe_form")
def test_save_api_recipe_success(mock_extract, mock_save, client):
    mock_extract.return_value = (True, "", "Pizza", ["dough", "cheese"], "Bake it", 123)
    
    response = client.post("/save_recipe", data={
        "name": "Pizza",
        "ingredients": "dough, cheese",
        "instructions": "Bake it",
        "api_id": "123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    mock_save.assert_called_once_with("Pizza", ["dough", "cheese"], "Bake it", source="api", api_id=123)

@patch("app.routes.extract_api_recipe_form")
def test_save_api_recipe_validation_error(mock_extract, client):
    """testing saving API recipe shows error on validation failure"""
    mock_extract.return_value = (False, "Invalid data", None, None, None, None)
    response = client.post("/save_recipe", data={
        "name": "",
        "api_id": "123"
    }, headers={"Referer": "/results"})
    assert response.status_code == 302


# ------- tests ingredient suggestions route -----
@patch("app.routes.get_ingredient_suggestions")
def test_ingredient_suggestions(mock_suggest, client):
    """testing /ingredient_suggestions endpoint returns JSON suggestions"""
    mock_suggest.return_value = ["tomato", "tofu", "tortilla"]
    
    response = client.get("/ingredient_suggestions?query=to")
    assert response.status_code == 200
    data = response.get_json()
    assert "tomato" in data
    assert "tofu" in data
    assert len(data) == 3

# ----------- health route tests ------------

def test_health_integration(client):
    """integration test for /health route"""
    resp = client.get("/health")
    data = resp.get_json()

    assert resp.status_code in (200, 500)
    assert "status" in data
    assert "details" in data
    assert "database" in data["details"]

