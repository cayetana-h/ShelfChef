
import pytest
from unittest.mock import patch, MagicMock
from app import api_client



@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("Tomatoes", "tomato"),
        ("tomato", "tomato"),
        ("  Onion  ", "onion"),
        ("Onions", "onion"),
        ("Eggs", "egg"),
        ("Berries", "berry"),
        ("Cherries", "cherry"),
        ("dishes", "dish"),
        ("Glasses", "glass"),   
        ("Kiwi", "kiwi"),       
        ("fish", "fish"),      
        ("Potatoes", "potato"), 
        ("Boxes", "box"),
    ]
)
def test_normalize_ingredient_extended(input_text, expected):
    assert api_client.normalize_ingredient(input_text) == expected



@patch("app.api_client.requests.get")
def test_search_recipes_success(mock_get):
    mock_response_main = MagicMock()
    mock_response_main.status_code = 200
    mock_response_main.json.return_value = [
        {"id": 1, "title": "Pizza", "usedIngredients": [{"name": "cheese"}], "missedIngredients": [{"name": "tomato"}]}
    ]
    
    mock_response_details = MagicMock()
    mock_response_details.status_code = 200
    mock_response_details.json.return_value = {
        "title": "Pizza",
        "instructions": "Bake it",
        "image": "pizza.png",
        "sourceUrl": "http://example.com",
        "extendedIngredients": [{"name": "cheese"}, {"name": "tomato"}]
    }

    mock_get.side_effect = [mock_response_main, mock_response_details]

    recipes = api_client.search_recipes(["cheese", "tomato"])
    assert len(recipes) == 1
    r = recipes[0]
    assert r["name"] == "Pizza"
    assert "cheese" in r["ingredients"]
    assert "tomato" in r["ingredients"]
    assert r["instructions"] == "Bake it"
    assert r["image"] == "pizza.png"
    assert r["sourceUrl"] == "http://example.com"
    assert r["missing_ingredients"] == 1

@patch("app.api_client.requests.get")
def test_search_recipes_api_failure(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    recipes = api_client.search_recipes(["cheese"])
    assert recipes == []


@patch("app.api_client.requests.get")
def test_get_recipe_details_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "title": "Salad",
        "instructions": "Mix it",
        "image": "salad.png",
        "sourceUrl": "http://example.com",
        "extendedIngredients": [{"name": "lettuce"}, {"name": "tomato"}]
    }
    mock_get.return_value = mock_response

    r = api_client.get_recipe_details(42)
    assert r["name"] == "Salad"
    assert "lettuce" in r["ingredients"]
    assert "tomato" in r["ingredients"]

@patch("app.api_client.requests.get")
def test_get_recipe_details_failure(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    r = api_client.get_recipe_details(999)
    assert r is None


@patch("sqlite3.connect")
def test_get_common_ingredients_from_db(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("Tomatoes",), ("Onion",)]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    ingredients = api_client.get_common_ingredients_from_db()
    assert "tomato" in ingredients
    assert "onion" in ingredients


@patch("sqlite3.connect")
def test_get_ingredient_suggestions_db_hit(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("Tomato",), ("Tomatillo",)]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    api_client.ingredient_cache.clear()
    suggestions = api_client.get_ingredient_suggestions("tom")
    assert "tomato" in suggestions
    assert "tomatillo" in suggestions

@patch("requests.get")
@patch("sqlite3.connect")
def test_get_ingredient_suggestions_api_fallback(mock_connect, mock_requests):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"name": "cucumber"}, {"name": "carrot"}]
    mock_requests.return_value = mock_resp

    api_client.ingredient_cache.clear()
    suggestions = api_client.get_ingredient_suggestions("cu")
    assert "cucumber" in suggestions
    assert "carrot" in suggestions

def test_get_ingredient_suggestions_empty_query():
    with patch("app.api_client.get_common_ingredients_from_db") as mock_common:
        mock_common.return_value = ["salt", "pepper"]
        suggestions = api_client.get_ingredient_suggestions("")
        assert "salt" in suggestions
        assert "pepper" in suggestions
