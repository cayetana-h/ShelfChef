import pytest
from unittest.mock import patch, MagicMock
from app import api_client, create_app


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
    """testing normalize_ingredient with extended cases"""
    from app.utils import normalize_ingredient
    assert normalize_ingredient(input_text) == expected


# ------ search_recipes tests ------- #
@patch("app.api_client.get_recipes_from_cache")
@patch("app.api_client.fetch_recipes_from_api")
@patch("app.api_client.save_recipes_to_cache")
def test_search_recipes_success(mock_save, mock_api, mock_cache):
    """ testing search_recipes retrieves from cache when available """
    mock_cache.return_value = [{"id": 1, "missing_ingredients": 0}]
    mock_config = {"SPOONACULAR_API_KEY": "test_key"}
    
    recipes = api_client.search_recipes(["cheese", "tomato"], config=mock_config)
    assert len(recipes) == 1
    mock_api.assert_not_called()
    mock_save.assert_not_called()
    

@patch("app.api_client.get_recipes_from_cache")
@patch("app.api_client.fetch_recipes_from_api")
@patch("app.api_client.save_recipes_to_cache")
def test_search_recipes_api_call(mock_save, mock_api, mock_cache):
    """testing search_recipes fetches from API and caches results when cache miss"""
    mock_cache.return_value = None
    mock_api.return_value = [
        {"id": 1, "missing_ingredients": 1},
        {"id": 2, "missing_ingredients": 0},
    ]
    mock_config = {"SPOONACULAR_API_KEY": "test_key"}
    
    recipes = api_client.search_recipes(["cheese"], config=mock_config)
    assert recipes[0]["id"] == 2  
    mock_save.assert_called_once()


# ------ get_recipe_details tests ------- #
@patch("app.api_client.fetch_recipe_details")
def test_get_recipe_details_success(mock_fetch):
    """testing get_recipe_details processes API response correctly"""
    mock_fetch.return_value = {
        "title": "Salad",
        "instructions": "Mix it",
        "image": " salad.png ",
        "sourceUrl": "http://example.com",
        "extendedIngredients": [{"name": "lettuce"}, {"name": "tomato"}]
    }
    mock_config = {"SPOONACULAR_API_KEY": "test_key"}
    
    result = api_client.get_recipe_details(42, config=mock_config)
    assert result["name"] == "Salad"
    assert "lettuce" in result["ingredients"]
    assert result["image"] == "salad.png"  


@patch("app.api_client.fetch_recipe_details")
def test_get_recipe_details_failure(mock_fetch):
    """testing get_recipe_details handles API failure gracefully"""
    mock_fetch.return_value = None
    mock_config = {"SPOONACULAR_API_KEY": "test_key"}
    
    result = api_client.get_recipe_details(999, config=mock_config)
    assert result is None


# ------ get_ingredient_suggestions tests ------- #
@patch("app.api_client.save_cached_response")
@patch("app.api_client.get_common_ingredients_from_db")
@patch("app.api_client.fetch_ingredient_suggestions_from_api")
@patch("app.api_client.get_ingredient_suggestions_from_cache")
def test_get_ingredient_suggestions_api_fallback(mock_cache, mock_api, mock_db, mock_save):
    """testing ingredient suggestions falls back to API when cache and DB miss"""
    app = create_app()
    with app.app_context():
        app.ingredient_cache = {}
        mock_cache.return_value = None
        mock_db.return_value = []
        mock_api.return_value = ["cucumber", "carrot"]
        
        suggestions = api_client.get_ingredient_suggestions("cu")
        assert "cucumber" in suggestions
        assert "carrot" in suggestions
        mock_api.assert_called_once()


@patch("app.api_client.get_common_ingredients_from_db")
def test_get_ingredient_suggestions_empty_query(mock_db):
    """testing ingredient suggestions with empty query returns all from DB"""
    app = create_app()
    with app.app_context():
        app.ingredient_cache = {}
        mock_db.return_value = ["salt", "pepper"]
        
        suggestions = api_client.get_ingredient_suggestions("")
        assert "salt" in suggestions
        assert "pepper" in suggestions