import pytest
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    """used to create a test client"""
    with app.test_client() as client:
        with app.app_context():
            yield client

# ----------- results routes tests ------------
def test_results_normalizes_ingredients(client):
    """route should call normalize_ingredients with raw input"""
    with patch("app.routes.normalize_ingredients") as mock_norm, \
         patch("app.routes.get_processed_recipes") as mock_process:
        mock_norm.return_value = ["tomato", "cheese"]
        mock_process.return_value = []

        client.get("/results?ingredients=Tomatoes, Cheeses")
        mock_norm.assert_called_once_with("Tomatoes, Cheeses")
        mock_process.assert_called_once()

def test_results_passes_sort_parameter(client):
    """route should forward sort_by correctly to get_processed_recipes"""
    with patch("app.routes.normalize_ingredients", return_value=["tomato"]), \
         patch("app.routes.get_processed_recipes") as mock_process:
        mock_process.return_value = []

        client.get("/results?ingredients=tomato&sort_by=matches")

        args = mock_process.call_args[0]
        assert args[1] == "matches"

def test_results_uses_recipe_cache(client, app):
    """route should use app.recipe_cache"""
    app.recipe_cache = {}
    with patch("app.routes.normalize_ingredients", return_value=["tomato"]), \
         patch("app.routes.get_processed_recipes", return_value=[]):
        client.get("/results?ingredients=tomato")


# ----------- recipe detail route tests ------------
def test_recipe_detail_handles_value_error(client):
    """route should return 404 when fetch raises ValueError"""
    with patch("app.routes.fetch_recipe_or_404", side_effect=ValueError("Not found")):
        resp = client.get("/recipe/999")
        assert resp.status_code == 404

def test_recipe_detail_preserves_query_params(client):
    """route should preserve query params in template"""
    with patch("app.routes.fetch_recipe_or_404", return_value={"name": "Test"}), \
         patch("app.routes.render_template") as mock_render:
        mock_render.return_value = "rendered"
        client.get("/recipe/123?ingredients=tomato&sort_by=matches")

        kwargs = mock_render.call_args[1]
        assert kwargs["ingredients"] == "tomato"
        assert kwargs["sort_by"] == "matches"


# ----------- new recipe route tests ------------
def test_new_recipe_get_renders_empty_form(client):
    """"route should render form with no recipe on GET"""
    with patch("app.routes.render_template") as mock_render:
        mock_render.return_value = "form"
        client.get("/my_recipes/new")
        assert mock_render.call_args[1]["recipe"] is None

def test_new_recipe_post_strips_and_titles_name(client):
    """"route should title case and strip recipe name on POST"""
    with patch("app.routes.process_new_recipe_form", return_value=(True, "", ["flour"], "Bake")), \
         patch("app.routes.RecipeStorage.save_user_recipe") as mock_save:
        client.post("/my_recipes/new", data={
            "name": "  whole wheat bread  ",
            "ingredients": "flour",
            "instructions": "Bake"
        })
        saved_name = mock_save.call_args[0][0]
        assert saved_name == "Whole Wheat Bread"

def test_new_recipe_validation_failure_redisplays_form(client):
    """route should flash error and re-render form on validation failure"""
    with patch("app.routes.process_new_recipe_form", return_value=(False, "Missing ingredients", None, None)), \
         patch("app.routes.flash") as mock_flash, \
         patch("app.routes.render_template") as mock_render:
        mock_render.return_value = "form"
        client.post("/my_recipes/new", data={"name": "Test"})
        mock_flash.assert_called_once_with("Missing ingredients", "error")


# ----------- edit recipe route tests ------------
def test_edit_recipe_rejects_non_user_recipes(client):
    """route should return 403 when editing non-user recipe"""
    with patch("app.routes.RecipeStorage.get_user_recipe", return_value={"id": 1, "source": "api"}):
        resp = client.get("/my_recipes/1/edit")
        assert resp.status_code == 403

def test_edit_recipe_post_titles_and_strips_name(client):
    """route should title case and strip recipe name on edit POST"""
    with patch("app.routes.RecipeStorage.get_user_recipe", return_value={"id": 1, "source": "user"}), \
         patch("app.routes.process_new_recipe_form", return_value=(True, "", ["pasta"], "Cook")), \
         patch("app.routes.RecipeStorage.update_user_recipe") as mock_update:
        mock_update.return_value = True
        client.post("/my_recipes/1/edit", data={
            "name": "  spaghetti carbonara  ",
            "ingredients": "pasta",
            "instructions": "Cook"
        })
        saved_name = mock_update.call_args[0][1]
        assert saved_name == "Spaghetti Carbonara"

def test_edit_recipe_handles_update_failure(client):
    """"route should flash error if update fails"""
    with patch("app.routes.RecipeStorage.get_user_recipe", return_value={"id": 1, "source": "user"}), \
         patch("app.routes.process_new_recipe_form", return_value=(True, "", ["pasta"], "Cook")), \
         patch("app.routes.RecipeStorage.update_user_recipe", return_value=False), \
         patch("app.routes.flash") as mock_flash, \
         patch("app.routes.render_template", return_value="form"):
        client.post("/my_recipes/1/edit", data={
            "name": "Pasta",
            "ingredients": "pasta",
            "instructions": "Cook"
        })
        mock_flash.assert_called_once_with("Unable to update recipe.", "error")


# ----------- save api recipe route tests ------------
def test_save_recipe_uses_api_source(client):
    """route should save recipe with source 'api' and correct api_id"""
    with patch("app.routes.extract_api_recipe_form", return_value=(True, "", "Pizza", ["dough"], "Bake", 123)), \
         patch("app.routes.RecipeStorage.save_user_recipe") as mock_save:
        client.post("/save_recipe", data={"api_id": "123"})
        kwargs = mock_save.call_args[1]
        assert kwargs["source"] == "api"
        assert kwargs["api_id"] == 123

def test_save_recipe_validation_failure_redirects(client):
    with patch("app.routes.extract_api_recipe_form", return_value=(False, "Invalid data", None, None, None, None)), \
         patch("app.routes.flash") as mock_flash:
        resp = client.post("/save_recipe", headers={"Referer": "/results"})
        assert resp.status_code == 302
        mock_flash.assert_called_once_with("Invalid data", "error")


# ----------- ingredient suggestions route tests ------------
def test_ingredient_suggestions_strips_query(client):
    with patch("app.routes.get_ingredient_suggestions") as mock_suggest:
        client.get("/ingredient_suggestions?query=  tomato  ")
        mock_suggest.assert_called_once_with("tomato")

def test_ingredient_suggestions_returns_json(client):
    """route should return JSON list of suggestions"""
    with patch("app.routes.get_ingredient_suggestions", return_value=["tomato", "tofu"]):
        resp = client.get("/ingredient_suggestions?query=to")
        assert resp.content_type == "application/json"
        assert isinstance(resp.get_json(), list)


# ----------- health route tests ------------

def test_health_unit_ok(client):
    with patch("app.storage.db.session") as mock_session:
        mock_conn = mock_session.bind
        mock_conn.execute.return_value = None

        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["details"]["database"] == "ok"
