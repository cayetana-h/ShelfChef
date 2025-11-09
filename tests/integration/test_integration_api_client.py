import pytest
from app import create_app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


# ------- tests for /results route -----
@patch("app.routes.get_processed_recipes")
def test_results_endpoint(mock_process, client):
    """testing /results endpoint returns recipe results in HTML"""
    mock_process.return_value = [
        {
            "name": "Pizza",
            "id": 123,
            "matches": ["cheese", "tomato"],
            "missing_count": 1,
            "image": "pizza.jpg"
        }
    ]
    response = client.get("/results?ingredients=cheese,tomato&sort_by=weighted")
    assert response.status_code == 200
    
    assert mock_process.called
    assert b"Pizza" in response.data
    assert b"cheese" in response.data
    assert b"tomato" in response.data


# ------- tests /recipe/<id> route -------
@patch("app.routes.fetch_recipe_or_404")
def test_recipe_details_endpoint(mock_fetch, client):
    """testing /recipe/<id> endpoint returns recipe details in HTML"""
    mock_fetch.return_value = {
        "name": "Salad",
        "instructions": "Mix it",
        "image": "salad.png",
        "sourceUrl": "http://example.com",
        "ingredients": ["lettuce", "tomato"],
    }
    response = client.get("/recipe/42")
    assert response.status_code == 200
    assert b"Salad" in response.data
    assert b"Mix it" in response.data


# ------ tests /ingredients endpoint ------
@patch("app.routes.get_ingredient_suggestions")
def test_ingredient_suggestions_endpoint(mock_suggest, client):
    """testing /ingredient_suggestions endpoint returns JSON suggestions"""
    mock_suggest.return_value = ["cucumber", "carrot"]
    response = client.get("/ingredient_suggestions?query=cu")
    assert response.status_code == 200
    data = response.get_json()
    assert "cucumber" in data
    assert "carrot" in data