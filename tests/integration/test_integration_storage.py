import pytest
from app import create_app
from app.storage import RecipeStorage, get_common_ingredients_from_db, init_db, db
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_app():
    """Creates a Flask app with in-memory SQLite DB for testing."""
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def sample_recipe():
    return {
        "name": "Test Soup",
        "ingredients": ["water", "salt"],
        "instructions": "Boil water. Add salt.",
        "source": "user",
        "api_id": None
    }


# ---------- RecipeStorage save/get ----------
def test_save_and_get_user_recipe(test_app):
    recipe = sample_recipe()
    recipe_id = RecipeStorage.save_user_recipe(**recipe)
    fetched = RecipeStorage.get_user_recipe(recipe_id)

    assert fetched is not None
    assert fetched['id'] == recipe_id
    assert fetched['name'] == recipe['name']
    assert fetched['ingredients'] == recipe['ingredients']
    assert fetched['instructions'] == recipe['instructions']
    assert fetched['source'] == "user"
    assert fetched['editable'] is True


def test_save_recipe_with_api_source(test_app):
    rid = RecipeStorage.save_user_recipe(
        "API Pizza",
        ["dough", "cheese"],
        "Bake at 400F",
        source="api",
        api_id=123
    )
    fetched = RecipeStorage.get_user_recipe(rid)
    assert fetched['source'] == 'api'
    assert fetched['api_id'] == 123
    assert fetched['editable'] is False


# ---------- update ----------
def test_update_user_recipe(test_app):
    rid = RecipeStorage.save_user_recipe(**sample_recipe())
    updated = RecipeStorage.update_user_recipe(rid, "New Name", ["pepper"], "New instructions")
    fetched = RecipeStorage.get_user_recipe(rid)

    assert updated is True
    assert fetched['name'] == "New Name"
    assert fetched['ingredients'] == ["pepper"]
    assert fetched['instructions'] == "New instructions"


def test_update_nonexistent_recipe_returns_false(test_app):
    assert RecipeStorage.update_user_recipe(999, "X", ["Y"], "Z") is False


def test_update_api_recipe_returns_false(test_app):
    rid = RecipeStorage.save_user_recipe(
        "API Recipe", ["a"], "b", source="api", api_id=1
    )
    updated = RecipeStorage.update_user_recipe(rid, "X", ["Y"], "Z")
    fetched = RecipeStorage.get_user_recipe(rid)

    assert updated is False
    assert fetched['editable'] is False
    assert fetched['name'] == "API Recipe"


# ---------- delete ----------
def test_delete_user_recipe(test_app):
    rid = RecipeStorage.save_user_recipe(**sample_recipe())
    assert RecipeStorage.delete_user_recipe(rid) is True
    assert RecipeStorage.get_user_recipe(rid) is None


def test_delete_nonexistent_recipe_returns_false(test_app):
    assert RecipeStorage.delete_user_recipe(999) is False


# ---------- get_user_recipes ----------
def test_get_user_recipes_returns_all(test_app):
    RecipeStorage.save_user_recipe("User Recipe", ["x"], "Y", source="user")
    RecipeStorage.save_user_recipe("API Recipe", ["a"], "B", source="api", api_id=1)
    recipes = RecipeStorage.get_user_recipes()
    assert len(recipes) == 2


def test_get_user_recipe_missing_returns_none(test_app):
    assert RecipeStorage.get_user_recipe(999) is None


# ---------- full lifecycle ----------
def test_recipe_full_lifecycle(test_app):
    rid = RecipeStorage.save_user_recipe("Original", ["a"], "Instructions")
    RecipeStorage.update_user_recipe(rid, "Updated", ["b"], "New instructions")
    fetched = RecipeStorage.get_user_recipe(rid)
    assert fetched['name'] == "Updated"
    RecipeStorage.delete_user_recipe(rid)
    assert RecipeStorage.get_user_recipe(rid) is None