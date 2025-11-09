import pytest
import json
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from app.utils import (
    get_cached_response,
    save_cached_response,
    validate_recipe_form,
    get_processed_recipes,
    fetch_recipe_or_404,
    extract_api_recipe_form,
    process_new_recipe_form,
    get_recipes_from_cache,
    fetch_recipes_from_api,
    save_recipes_to_cache,
    fetch_recipe_details,
    fetch_ingredient_suggestions_from_api,
    get_ingredient_suggestions_from_cache,
    save_ingredient_suggestions_to_cache
)


# ----------  db tests ---------- #
class MockConnection:
    """mocking sqlite3 connection"""
    def __init__(self, real_conn):
        self._conn = real_conn
        self.row_factory = real_conn.row_factory
    
    def cursor(self):
        return self._conn.cursor()
    
    def commit(self):
        return self._conn.commit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def real_close(self):
        self._conn.close()

@contextmanager
def mock_db_connection(mock_conn):
    yield mock_conn

@pytest.fixture
def in_memory_db():
    """setting up in-memory sqlite db for tests"""
    real_conn = sqlite3.connect(":memory:")
    real_conn.row_factory = sqlite3.Row
    
    c = real_conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cached_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT UNIQUE NOT NULL,
            response TEXT NOT NULL
        )
    """)
    real_conn.commit()
    
    mock_conn = MockConnection(real_conn)
    
    with patch("app.utils.db_connection", lambda: mock_db_connection(mock_conn)):
        yield mock_conn
    
    mock_conn.real_close()


def test_get_cached_response_exists(in_memory_db):
    """testing retrieving existing cached response"""
    c = in_memory_db.cursor()
    c.execute("INSERT INTO cached_responses (query, response) VALUES (?, ?)", 
              ("test_query", '{"result": "data"}'))
    in_memory_db.commit()
    
    result = get_cached_response("test_query")
    assert result == '{"result": "data"}'

def test_get_cached_response_not_exists(in_memory_db):
    result = get_cached_response("nonexistent")
    assert result is None

def test_save_cached_response_new(in_memory_db):
    save_cached_response("new_query", '{"data": "value"}')  
    result = get_cached_response("new_query")
    assert result == '{"data": "value"}'

def test_save_cached_response_update(in_memory_db):
    save_cached_response("query", '{"old": "data"}')
    save_cached_response("query", '{"new": "data"}')
    result = get_cached_response("query")
    assert result == '{"new": "data"}'

def test_get_recipes_from_cache_with_data(in_memory_db):
    recipes = [{"id": 1, "name": "Pizza"}]
    save_cached_response("tomato,cheese", json.dumps(recipes))
    
    result = get_recipes_from_cache("tomato,cheese")
    assert result == recipes

def test_get_recipes_from_cache_no_data(in_memory_db):
    result = get_recipes_from_cache("nonexistent")
    assert result is None

def test_get_recipes_from_cache_invalid_json(in_memory_db):
    """testing handling invalid JSON in cache"""
    c = in_memory_db.cursor()
    c.execute("INSERT INTO cached_responses (query, response) VALUES (?, ?)",
              ("bad_query", "invalid json{"))
    in_memory_db.commit()
    
    result = get_recipes_from_cache("bad_query")
    assert result is None

def test_save_recipes_to_cache(in_memory_db):
    recipes = [{"id": 1, "name": "Pizza"}, {"id": 2, "name": "Pasta"}]
    save_recipes_to_cache("tomato,cheese", recipes)
    
    result = get_recipes_from_cache("tomato,cheese")
    assert result == recipes


# ----------  validate_recipe_form tests ----------
def test_validate_recipe_form_all_valid():
    """ validation with all valid inputs"""
    valid, msg, ingredients, instructions = validate_recipe_form("Pizza", "tomato, cheese, basil", ["Mix ingredients", "Bake"])
    
    assert valid is True
    assert msg == ""
    assert set(ingredients) == {"basil", "cheese", "tomato"}
    assert "1. Mix ingredients" in instructions
    assert "2. Bake" in instructions

def test_validate_recipe_form_empty_name():
    """ validation with empty name"""
    valid, msg, ingredients, instructions = validate_recipe_form("", "tomato, cheese", ["Mix", "Bake"])
    
    assert valid is False
    assert "name cannot be empty" in msg

def test_validate_recipe_form_no_ingredients():
    """ validation with no ingredients"""
    valid, msg, ingredients, instructions = validate_recipe_form("Pizza", "", ["Mix", "Bake"])
    
    assert valid is False
    assert "at least one ingredient" in msg

def test_validate_recipe_form_no_instructions():
    """ validation with no instructions"""
    valid, msg, ingredients, instructions = validate_recipe_form("Pizza", "tomato, cheese", ["", "  "])
    
    assert valid is False
    assert "provide instructions" in msg

def test_validate_recipe_form_long_name():
    """ validation with name exceeding max length"""
    long_name = "a" * 101
    valid, msg, ingredients, instructions = validate_recipe_form(long_name, "tomato",["Mix"])
    
    assert valid is False
    assert "cannot exceed" in msg


# ---------- get_processed_recipes tests----------
def test_get_processed_recipes_from_cache():
    """ retrieving recipes from cache"""
    cache = {}
    user_ingredients = ["tomato", "cheese"]
    cached_recipes = [
        {"id": 1, "ingredients": ["tomato", "cheese", "basil"], 
         "matches": ["tomato", "cheese"], "missing_count": 1}
    ]
    cache[("tomato", "cheese")] = cached_recipes
    
    with patch("app.api_client.search_recipes") as mock_search:
        result = get_processed_recipes(user_ingredients, "matches", cache)
    
    mock_search.assert_not_called()
    assert len(result) == 1

def test_get_processed_recipes_from_api():
    """fetching recipes from API when not in cache"""
    cache = {}
    user_ingredients = ["tomato"]
    api_results = [{"id": 1, "name": "Pizza", "ingredients": ["tomato", "cheese"]}]
    
    with patch("app.api_client.search_recipes", return_value=api_results):
        result = get_processed_recipes(user_ingredients, "matches", cache)
    
    assert len(result) == 1
    assert ("tomato",) in cache

def test_get_processed_recipes_sorts_correctly():
    """happy path sorting by matches"""
    cache = {}
    api_results = [
        {"id": 1, "ingredients": ["tomato"]},
        {"id": 2, "ingredients": ["tomato", "cheese", "basil"]},
        {"id": 3, "ingredients": ["tomato", "cheese"]}
    ]
    with patch("app.api_client.search_recipes", return_value=api_results):
        result = get_processed_recipes(["tomato"], "matches", cache)
    
    assert result[0]["id"] == 1 

def test_get_processed_recipes_doesnt_modify_cache():
    """ ensuring cache is not modified unexpectedly"""
    cache = {}
    api_results = [
        {"id": 1, "ingredients": ["tomato", "cheese"]},
        {"id": 2, "ingredients": ["tomato"]}
    ]
    with patch("app.api_client.search_recipes", return_value=api_results):
        get_processed_recipes(["tomato"], "matches", cache)
        result2 = get_processed_recipes(["tomato"], "missing", cache)
    
    assert len(result2) == 2


# ---------- fetch_recipe_or_404 tests ----------
def test_fetch_recipe_or_404_success():
    """fetching existing recipe"""
    mock_recipe = {"id": 123, "name": "Pizza"}
    with patch("app.api_client.get_recipe_details", return_value=mock_recipe):
        result = fetch_recipe_or_404(123)
    
    assert result == mock_recipe

def test_fetch_recipe_or_404_not_found():
    """fetching non-existing recipe"""
    with patch("app.api_client.get_recipe_details", return_value=None):
        with pytest.raises(ValueError, match="Recipe 123 not found"):
            fetch_recipe_or_404(123)


# ---------- extract_api_recipe_form tests ----------

def test_extract_api_recipe_form_valid():
    """happy path extraction"""
    form = {
        "name": "  pizza  ",
        "ingredients": "tomato, cheese",
        "instructions": "Mix\nBake",
        "api_id": "123"
    }
    valid, msg, name, ingredients, instructions, api_id = extract_api_recipe_form(form)
    
    assert valid is True
    assert name == "Pizza"
    assert set(ingredients) == {"cheese", "tomato"}
    assert "1. Mix" in instructions
    assert api_id == 123

def test_extract_api_recipe_form_invalid_api_id():
    """invalid api_id handling"""
    form = {
        "name": "Pizza",
        "ingredients": "tomato",
        "instructions": "Bake",
        "api_id": "not_a_number"
    }
    valid, msg, name, ingredients, instructions, api_id = extract_api_recipe_form(form)
    
    assert api_id is None

def test_extract_api_recipe_form_validation_failure():
    """field validation failure handling"""
    form = {
        "name": "",
        "ingredients": "tomato",
        "instructions": "Bake",
        "api_id": "123"
    }
    valid, msg, name, ingredients, instructions, api_id = extract_api_recipe_form(form)
    
    assert valid is False
    assert msg != ""


# ----------  process_new_recipe_form tests ----------
def test_process_new_recipe_form_valid():
    """happy path processing"""
    form_data = Mock()
    form_data.get.side_effect = lambda key, default="": {
        "name": "  pasta  ",
        "ingredients": "tomato, basil"
    }.get(key, default)
    form_data.getlist.return_value = ["Boil water", "Add pasta", ""]
    valid, msg, ingredients, instructions = process_new_recipe_form(form_data)
    
    assert valid is True
    assert msg == ""
    assert "Pasta" in form_data.get("name", "").title()
    assert set(ingredients) == {"basil", "tomato"}
    assert "1. Boil water" in instructions

def test_process_new_recipe_form_validation_failure():
    """handling validation failure"""
    form_data = Mock()
    form_data.get.side_effect = lambda key, default="": {
        "name": "",
        "ingredients": "tomato"
    }.get(key, default)
    form_data.getlist.return_value = ["Mix"]
    valid, msg, ingredients, instructions = process_new_recipe_form(form_data)
    
    assert valid is False
    assert "cannot be empty" in msg


# ----------  fetch_recipes_from_api tests ----------
def test_fetch_recipes_from_api_success():
    """happy path fetching recipes"""
    config = {
        "API_URL": "http://api.test/recipes",
        "RECIPE_DETAILS_URL": "http://api.test/recipes/{id}",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    search_response = Mock()
    search_response.status_code = 200
    search_response.json.return_value = [
        {"id": 1, "title": "Pizza", "usedIngredients": [], "missedIngredients": []}
    ]
    
    details_response = Mock()
    details_response.status_code = 200
    details_response.json.return_value = {
        "instructions": "Bake it",
        "image": "pizza.jpg"
    }
    
    mock_requester.get.side_effect = [search_response, details_response]
    result = fetch_recipes_from_api("tomato", 10, config, mock_requester)
    assert len(result) == 1
    assert result[0]["name"] == "Pizza"

def test_fetch_recipes_from_api_failure():
    """handling API failure"""
    config = {
        "API_URL": "http://api.test/recipes",
        "RECIPE_DETAILS_URL": "http://api.test/recipes/{id}",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    response = Mock()
    response.status_code = 500
    mock_requester.get.return_value = response
    result = fetch_recipes_from_api("tomato", 10, config, mock_requester)
    assert result == []

def test_fetch_recipes_from_api_details_failure():
    """handling recipe details fetch failure"""
    config = {
        "API_URL": "http://api.test/recipes",
        "RECIPE_DETAILS_URL": "http://api.test/recipes/{id}",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    search_response = Mock()
    search_response.status_code = 200
    search_response.json.return_value = [
        {"id": 1, "title": "Pizza", "usedIngredients": [], "missedIngredients": []}
    ]
    
    details_response = Mock()
    details_response.status_code = 404
    
    mock_requester.get.side_effect = [search_response, details_response]
    result = fetch_recipes_from_api("tomato", 10, config, mock_requester)
    
    assert len(result) == 1
    assert result[0]["instructions"] == ""


# ---------- fetch_recipe_details tests ----------
def test_fetch_recipe_details_success():
    """happy path fetching recipe details"""
    config = {
        "RECIPE_DETAILS_URL": "http://api.test/recipes/{id}",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"title": "Pizza", "image": "pizza.jpg"}
    mock_requester.get.return_value = response
    
    result = fetch_recipe_details(123, config, mock_requester)
    assert result["title"] == "Pizza"

def test_fetch_recipe_details_failure():
    """handling recipe details fetch failure"""
    config = {
        "RECIPE_DETAILS_URL": "http://api.test/recipes/{id}",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    response = Mock()
    response.status_code = 404
    mock_requester.get.return_value = response
    result = fetch_recipe_details(123, config, mock_requester)
    assert result is None


# ---------- fetch_ingredient_suggestions_from_api tests ----------
def test_fetch_ingredient_suggestions_success():
    """happy path fetching suggestions"""
    config = {
        "INGREDIENT_AUTOCOMPLETE_URL": "http://api.test/ingredients",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    response = Mock()
    response.status_code = 200
    response.json.return_value = [
        {"name": "tomatoes"},
        {"name": "tomato sauce"}
    ]
    mock_requester.get.return_value = response
    result = fetch_ingredient_suggestions_from_api("tom", config, mock_requester)
    assert "tomato" in result
    assert "tomato sauce" in result

def test_fetch_ingredient_suggestions_api_failure():
    """handling API failure during suggestions fetch"""
    config = {
        "INGREDIENT_AUTOCOMPLETE_URL": "http://api.test/ingredients",
        "API_KEY": "test_key"
    }
    
    mock_requester = Mock()
    response = Mock()
    response.status_code = 500
    mock_requester.get.return_value = response
    result = fetch_ingredient_suggestions_from_api("tom", config, mock_requester)
    assert result == []


# ----------  ingredient cache helpers tests----------
def test_get_ingredient_suggestions_from_cache():
    """cache hit for suggestions"""
    cache = {"tom": ["tomato", "tomato sauce"]}
    
    result = get_ingredient_suggestions_from_cache("tom", cache)
    assert result == ["tomato", "tomato sauce"]

def test_get_ingredient_suggestions_from_cache_miss():
    """cache miss for suggestions"""
    cache = {}
    
    result = get_ingredient_suggestions_from_cache("tom", cache)
    assert result is None

def test_save_ingredient_suggestions_to_cache():
    """saving suggestions to cache"""
    cache = {}
    suggestions = ["tomato", "tomato paste"]
    
    save_ingredient_suggestions_to_cache("tom", suggestions, cache)
    assert cache["tom"] == suggestions

def test_save_ingredient_suggestions_overwrites():
    """overwriting existing suggestions in cache"""
    cache = {"tom": ["old"]}
    suggestions = ["new"]
    
    save_ingredient_suggestions_to_cache("tom", suggestions, cache)
    assert cache["tom"] == ["new"]


# ---------- full thing ----------
def test_full_recipe_search_workflow():
    """happy path full recipe search workflow with caching"""
    cache = {}
    user_ingredients = ["tomato", "cheese"]
    key = tuple(user_ingredients)  

    api_results = [
        {"id": 1, "name": "Pizza", "ingredients": ["tomato", "cheese", "dough"]},
        {"id": 2, "name": "Salad", "ingredients": ["tomato", "lettuce"]}
    ]

    with patch("app.api_client.search_recipes", return_value=api_results):
        # first it should fetch from API
        result1 = get_processed_recipes(user_ingredients, "matches", cache)

        # then it should fetch from cache
        result2 = get_processed_recipes(user_ingredients, "missing", cache)

    assert len(result1) == 2
    assert len(result2) == 2
    ids1 = {r["id"] for r in result1}
    ids2 = {r["id"] for r in result2}
    assert ids1 == {1, 2}
    assert ids2 == {1, 2}

    assert key in cache
    cached_recipes = cache[key]
    cached_ids = {r["id"] for r in cached_recipes}
    
    assert cached_ids == {1, 2}
