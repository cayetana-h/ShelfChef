import pytest
import sqlite3
from unittest.mock import patch
from app import storage


class MockConnection:
    def __init__(self, real_conn):
        self._conn = real_conn
        self.row_factory = real_conn.row_factory
    
    def cursor(self):
        return self._conn.cursor()
    
    def commit(self):
        return self._conn.commit()
    
    def close(self):
        pass
    
    def real_close(self):
        self._conn.close()


@pytest.fixture
def in_memory_db():
    """Create a fresh in-memory database for each test."""
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
    real_conn.commit()
    
    mock_conn = MockConnection(real_conn)
    
    with patch("app.storage._get_connection", return_value=mock_conn):
        yield mock_conn
    
    mock_conn.real_close()


def sample_recipe():
    return {
        "name": "Test Soup",
        "ingredients": ["water", "salt"],
        "instructions": "Boil water. Add salt.",
        "source": "user",
        "api_id": None
    }


def test_save_and_get_user_recipe(in_memory_db):
    recipe = sample_recipe()
    recipe_id = storage.save_user_recipe(**recipe)
    fetched = storage.get_user_recipe(recipe_id)
    
    assert fetched is not None
    assert fetched["name"] == recipe["name"]
    assert fetched["ingredients"] == recipe["ingredients"]
    assert fetched["instructions"] == recipe["instructions"]
    assert fetched["source"] == "user"
    assert fetched["editable"] is True


def test_get_user_recipes_returns_list(in_memory_db):
    recipe = sample_recipe()
    storage.save_user_recipe(**recipe)
    recipes = storage.get_user_recipes()
    
    assert isinstance(recipes, list)
    assert len(recipes) == 1
    assert recipes[0]["name"] == recipe["name"]


def test_get_user_recipe_missing_returns_none(in_memory_db):
    result = storage.get_user_recipe(999)
    assert result is None


def test_update_user_recipe_success(in_memory_db):
    recipe = sample_recipe()
    rid = storage.save_user_recipe(**recipe)
    
    updated = storage.update_user_recipe(rid, "New Name", ["new ingredient"], "New instructions")
    assert updated is True
    
    fetched = storage.get_user_recipe(rid)
    assert fetched["name"] == "New Name"
    assert fetched["ingredients"] == ["new ingredient"]
    assert fetched["instructions"] == "New instructions"


def test_update_user_recipe_nonexistent_returns_false(in_memory_db):
    updated = storage.update_user_recipe(999, "X", ["Y"], "Z")
    assert updated is False


def test_update_user_recipe_api_source_returns_false(in_memory_db):
    rid = storage.save_user_recipe("API Recipe", ["a"], "b", source="api", api_id=1)
    
    updated = storage.update_user_recipe(rid, "X", ["Y"], "Z")
    assert updated is False
    
    fetched = storage.get_user_recipe(rid)
    assert fetched["name"] == "API Recipe"
    assert fetched["editable"] is False


def test_delete_user_recipe_success(in_memory_db):
    rid = storage.save_user_recipe(**sample_recipe())
    
    deleted = storage.delete_user_recipe(rid)
    assert deleted is True
    
    assert storage.get_user_recipe(rid) is None


def test_delete_user_recipe_nonexistent_returns_false(in_memory_db):
    deleted = storage.delete_user_recipe(999)
    assert deleted is False