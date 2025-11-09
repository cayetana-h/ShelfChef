import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from app.storage import (
    RecipeStorage, 
    DatabaseInitializer,
    get_common_ingredients_from_db,
    init_db
)


class MockConnection:
    """mock db for testing with in-memory sqlite3"""
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
    """used to patch db_connection context manager"""
    yield mock_conn


@pytest.fixture
def in_memory_db():
    """mock in-memory database fixture"""
    real_conn = sqlite3.connect(":memory:")
    real_conn.row_factory = sqlite3.Row
    
    c = real_conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS my_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ingredients TEXT,
            instructions TEXT,
            source TEXT DEFAULT 'user',
            api_id INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cached_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT UNIQUE NOT NULL,
            response TEXT NOT NULL
        )
    """)
    real_conn.commit()
    mock_conn = MockConnection(real_conn)
    
    # to patch the db_connection function to use mock connection
    with patch("app.storage.db_connection", lambda: mock_db_connection(mock_conn)):
        yield mock_conn
    
    mock_conn.real_close()


def sample_recipe():
    """just used to provide a sample recipe dict"""
    return {
        "name": "Test Soup",
        "ingredients": ["water", "salt"],
        "instructions": "Boil water. Add salt.",
        "source": "user",
        "api_id": None
    }


# ---------- save_user_recipe and get_user_recipe in RecipeStorage tests ----------
def test_save_and_get_user_recipe(in_memory_db):
    """simple save and get user recipe test"""
    recipe = sample_recipe()
    recipe_id = RecipeStorage.save_user_recipe(**recipe)
    assert recipe_id is not None
    assert recipe_id > 0
    
    fetched = RecipeStorage.get_user_recipe(recipe_id)
    assert fetched is not None
    assert fetched["id"] == recipe_id
    assert fetched["name"] == recipe["name"]
    assert fetched["ingredients"] == recipe["ingredients"]
    assert fetched["instructions"] == recipe["instructions"]
    assert fetched["source"] == "user"
    assert fetched["editable"] is True

def test_save_recipe_with_api_source(in_memory_db):
    """saving a recipe with source 'api' sets it to False"""
    recipe_id = RecipeStorage.save_user_recipe(
        name="API Pizza",
        ingredients=["dough", "cheese"],
        instructions="Bake at 400F",
        source="api",
        api_id=12345
    )
    fetched = RecipeStorage.get_user_recipe(recipe_id)
    
    assert fetched["source"] == "api"
    assert fetched["api_id"] == 12345
    assert fetched["editable"] is False

def test_save_recipe_strips_whitespace_from_ingredients(in_memory_db):
    """checking whitespace is stripped from ingredients"""
    recipe_id = RecipeStorage.save_user_recipe(
        name="Test",
        ingredients=[" salt ", "  pepper  ", "cumin"],
        instructions="Mix",
        source="user"
    )
    fetched = RecipeStorage.get_user_recipe(recipe_id)

    assert fetched["ingredients"] == ["salt", "pepper", "cumin"]

def test_save_recipe_filters_none_ingredients(in_memory_db):
    """testing none ingredients are filtered out"""
    recipe_id = RecipeStorage.save_user_recipe(
        name="Test",
        ingredients=["salt", None, "pepper", None],
        instructions="Mix",
        source="user"
    )
    fetched = RecipeStorage.get_user_recipe(recipe_id)

    assert fetched["ingredients"] == ["salt", "pepper"]


# ---------- get_user_recipes from RecipeStorage tests ----------
def test_get_user_recipes_returns_list(in_memory_db):
    """checking it returns a list of recipes"""
    recipe = sample_recipe()
    RecipeStorage.save_user_recipe(**recipe)
    recipes = RecipeStorage.get_user_recipes()
    
    assert isinstance(recipes, list)
    assert len(recipes) == 1
    assert recipes[0]["name"] == recipe["name"]

def test_get_user_recipes_empty_database(in_memory_db):
    recipes = RecipeStorage.get_user_recipes()
    assert recipes == []

def test_get_user_recipes_includes_both_user_and_api(in_memory_db):
    """testing both user and API recipes are returned"""
    RecipeStorage.save_user_recipe("User Recipe", ["a"], "User", source="user")
    RecipeStorage.save_user_recipe("API Recipe", ["b"], "API", source="api", api_id=1)
    
    recipes = RecipeStorage.get_user_recipes()
    assert len(recipes) == 2


# ---------- get_user_recipe from RecipeStorage test----------
def test_get_user_recipe_missing_returns_none(in_memory_db):
    result = RecipeStorage.get_user_recipe(999)
    assert result is None


# ---------- update_user_recipe from RecipeStorage tests ----------
def test_update_user_recipe_success(in_memory_db):
    """verifying successful update of a user recipe"""
    recipe = sample_recipe()
    rid = RecipeStorage.save_user_recipe(**recipe)
    
    updated = RecipeStorage.update_user_recipe(
        rid, 
        "New Name", 
        ["new ingredient"], 
        "New instructions"
    )
    
    assert updated is True
    
    fetched = RecipeStorage.get_user_recipe(rid)
    assert fetched["name"] == "New Name"
    assert fetched["ingredients"] == ["new ingredient"]
    assert fetched["instructions"] == "New instructions"

def test_update_user_recipe_nonexistent_returns_false(in_memory_db):
    """ non-existent recipe should return False"""
    updated = RecipeStorage.update_user_recipe(999, "X", ["Y"], "Z")
    assert updated is False

def test_update_user_recipe_api_source_returns_false(in_memory_db):
    """API-sourced recipes should not be updated"""
    rid = RecipeStorage.save_user_recipe(
        "API Recipe", 
        ["a"], 
        "b", 
        source="api", 
        api_id=1
    )
    updated = RecipeStorage.update_user_recipe(rid, "X", ["Y"], "Z")
    assert updated is False
    
    fetched = RecipeStorage.get_user_recipe(rid)
    assert fetched["name"] == "API Recipe"
    assert fetched["editable"] is False

def test_update_user_recipe_strips_whitespace(in_memory_db):
    """whitespace should be stripped from ingredients on update"""
    rid = RecipeStorage.save_user_recipe("Test", ["a"], "Instructions")
    RecipeStorage.update_user_recipe(rid, "Test", [" salt ", "  pepper  "], "New")
    fetched = RecipeStorage.get_user_recipe(rid)
    assert fetched["ingredients"] == ["salt", "pepper"]


# ---------- delete_user_recipe from RecipeStorage tests----------
def test_delete_user_recipe_success(in_memory_db):
    """happy path test for deleting a user recipe"""
    rid = RecipeStorage.save_user_recipe(**sample_recipe())
    deleted = RecipeStorage.delete_user_recipe(rid)
    assert deleted is True
    
    assert RecipeStorage.get_user_recipe(rid) is None

def test_delete_user_recipe_nonexistent_returns_false(in_memory_db):
    """deleting non-existent recipe returns False"""
    deleted = RecipeStorage.delete_user_recipe(999)
    assert deleted is False

def test_delete_api_recipe_succeeds(in_memory_db):
    """API recipes can be deleted (not like update)"""
    rid = RecipeStorage.save_user_recipe(
        "API Recipe", 
        ["a"], 
        "b", 
        source="api", 
        api_id=1
    )
    
    deleted = RecipeStorage.delete_user_recipe(rid)
    assert deleted is True


# ----------  ensure_db from DatabaseInitializer test ----------
def test_database_initializer_ensure_db(in_memory_db):
    """checking correct tables are created"""
    c = in_memory_db.cursor()
    
    tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='my_recipes'"
    ).fetchall()
    assert len(tables) == 1
    
    tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='cached_responses'"
    ).fetchall()
    assert len(tables) == 1

# ----------  get_common_ingredients_from_db  tests----------
def test_get_common_ingredients_from_db(in_memory_db):
    """test retrieving common ingredients from db"""
    c = in_memory_db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS ingredients (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("INSERT INTO ingredients (name) VALUES ('Tomato')")
    c.execute("INSERT INTO ingredients (name) VALUES ('CHEESE')")
    c.execute("INSERT INTO ingredients (name) VALUES ('  Basil  ')")
    in_memory_db.commit()
    
    with patch("app.storage.normalize_ingredient", side_effect=lambda x: x.strip().lower()):
        ingredients = get_common_ingredients_from_db()
    
    assert "tomato" in ingredients
    assert "cheese" in ingredients
    assert "basil" in ingredients

def test_get_common_ingredients_empty_table(in_memory_db):
    """test retrieving common ingredients from empty table"""
    c = in_memory_db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS ingredients (id INTEGER PRIMARY KEY, name TEXT)")
    in_memory_db.commit()
    
    with patch("app.storage.normalize_ingredient", side_effect=lambda x: x.strip().lower()):
        ingredients = get_common_ingredients_from_db()
    
    assert ingredients == []


# ----------  init_db tests ----------
def test_init_db_without_app(in_memory_db):
    """test initiliazing db without Flask app context"""
    with patch("app.storage.DatabaseInitializer.ensure_db") as mock_ensure:
        init_db(app=None)
        mock_ensure.assert_called_once()

def test_init_db_with_app():
    """test initiliazing db with Flask app context"""
    mock_app = MagicMock()
    with patch("app.storage.DatabaseInitializer.ensure_db") as mock_ensure:
        init_db(app=mock_app)
        mock_app.app_context.assert_called_once()


# ---------- full path ----------
def test_full_recipe_lifecycle(in_memory_db):
    """testing save, get, update, delete sequence happy path"""
    recipe_id = RecipeStorage.save_user_recipe(
        "Original Name",
        ["ingredient1", "ingredient2"],
        "Original instructions"
    )    
    recipe = RecipeStorage.get_user_recipe(recipe_id)
    assert recipe["name"] == "Original Name"
    
    RecipeStorage.update_user_recipe(
        recipe_id,
        "Updated Name",
        ["new_ingredient"],
        "Updated instructions"
    )
    recipe = RecipeStorage.get_user_recipe(recipe_id)
    assert recipe["name"] == "Updated Name"
    
    RecipeStorage.delete_user_recipe(recipe_id)
    recipe = RecipeStorage.get_user_recipe(recipe_id)
    assert recipe is None

# ---------- multiple ----------
def test_multiple_recipes_interaction(in_memory_db):
    """testing that multiple recipes can be handled correctly"""
    id1 = RecipeStorage.save_user_recipe("Recipe 1", ["a"], "Instructions 1")
    id2 = RecipeStorage.save_user_recipe("Recipe 2", ["b"], "Instructions 2")
    id3 = RecipeStorage.save_user_recipe("Recipe 3", ["c"], "Instructions 3")
    
    RecipeStorage.update_user_recipe(id2, "Updated 2", ["b", "x"], "New 2")
    RecipeStorage.delete_user_recipe(id3)
    
    r1 = RecipeStorage.get_user_recipe(id1)
    r2 = RecipeStorage.get_user_recipe(id2)
    r3 = RecipeStorage.get_user_recipe(id3)
    
    assert r1["name"] == "Recipe 1"
    assert r2["name"] == "Updated 2"
    assert r3 is None