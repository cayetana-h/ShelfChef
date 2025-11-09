import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.utils import (
    normalize_ingredients,
    build_cache_key,
    matching_missing_for_recipe,
    sort_recipes,
    validate_name,
    validate_ingredients,
    validate_instructions,
    format_instructions,
    normalize_ingredient,
    clean_instructions,
    prepare_ingredient_query,
    build_api_params,
    build_recipe_dict,
    build_recipe_details,
    init_cache
)


# ----------  normalize_ingredients tests  ----------
def test_normalize_ingredients_basic():
    result = normalize_ingredients("Tomato, Cheese, Basil")
    assert result == ["basil", "cheese", "tomato"]

def test_normalize_ingredients_with_whitespace():
    result = normalize_ingredients("  tomato  ,  cheese  ,  basil  ")
    assert result == ["basil", "cheese", "tomato"]

def test_normalize_ingredients_empty_string():
    result = normalize_ingredients("")
    assert result == []

def test_normalize_ingredients_with_empty_items():
    result = normalize_ingredients("tomato, , cheese, , basil")
    assert result == ["basil", "cheese", "tomato"]

def test_normalize_ingredients_case_insensitive():
    result = normalize_ingredients("TOMATO, ChEeSe, BaSiL")
    assert result == ["basil", "cheese", "tomato"]

def test_normalize_ingredients_sorted():
    result = normalize_ingredients("zebra, apple, mango")
    assert result == ["apple", "mango", "zebra"]


# ---------- build_cache_key tests ----------
def test_build_cache_key_creates_tuple():
    key = build_cache_key(["tomato", "cheese"])
    assert isinstance(key, tuple)
    assert key == ("tomato", "cheese")

def test_build_cache_key_empty_list():
    key = build_cache_key([])
    assert key == ()

def test_build_cache_key_single_item():
    key = build_cache_key(["tomato"])
    assert key == ("tomato",)

def test_build_cache_key_preserves_order():
    key1 = build_cache_key(["a", "b", "c"])
    key2 = build_cache_key(["c", "b", "a"])
    assert key1 != key2


# ---------- matching_missing_for_recipe tests ----------
def test_matching_missing_basic():
    """calculating matches and missing ingredients"""
    user_ingredients = ["tomato", "cheese"]
    recipes = [
        {"id": 1, "ingredients": ["tomato", "cheese", "basil"]}
    ]
    result = matching_missing_for_recipe(user_ingredients, recipes)
    
    assert len(result) == 1
    assert set(result[0]["matches"]) == {"tomato", "cheese"}
    assert result[0]["missing_count"] == 1

def test_matching_missing_case_insensitive():
    """testing that matching is case insensitive"""
    user_ingredients = ["tomato", "cheese"]
    recipes = [
        {"id": 1, "ingredients": ["TOMATO", "CHEESE", "Basil"]}
    ]
    result = matching_missing_for_recipe(user_ingredients, recipes)
    
    assert set(result[0]["matches"]) == {"tomato", "cheese"}

def test_matching_missing_no_matches():
    """when there are no maatches it should return empty matches and full missing count"""
    user_ingredients = ["tomato", "cheese"]
    recipes = [
        {"id": 1, "ingredients": ["apple", "banana"]}
    ]
    result = matching_missing_for_recipe(user_ingredients, recipes)
    
    assert result[0]["matches"] == []
    assert result[0]["missing_count"] == 2

def test_matching_missing_all_matches():
    """all ingredients match should yield zero missing"""
    user_ingredients = ["tomato", "cheese", "basil"]
    recipes = [
        {"id": 1, "ingredients": ["tomato", "cheese", "basil"]}
    ]
    result = matching_missing_for_recipe(user_ingredients, recipes)
    
    assert len(result[0]["matches"]) == 3
    assert result[0]["missing_count"] == 0

def test_matching_missing_empty_ingredients():
    """no ingredients in recipe should yield zero matches and zero missing"""
    user_ingredients = ["tomato", "cheese"]
    recipes = [
        {"id": 1, "ingredients": []}
    ]
    result = matching_missing_for_recipe(user_ingredients, recipes)
    assert result[0]["matches"] == []
    assert result[0]["missing_count"] == 0

def test_matching_missing_preserves_original():
    """original recipe dict should not be modified if no ingredients match"""
    user_ingredients = ["tomato"]
    recipes = [
        {"id": 1, "ingredients": ["tomato", "cheese"]}
    ]
    result = matching_missing_for_recipe(user_ingredients, recipes)
    
    assert "matches" not in recipes[0]
    assert "missing_count" not in recipes[0]


# ---------- sort_recipes tests ----------
def test_sort_recipes_by_matches():
    """it should sort by number of matches descending"""
    recipes = [
        {"id": 1, "matches": ["a"], "missing_count": 2},
        {"id": 2, "matches": ["a", "b", "c"], "missing_count": 0},
        {"id": 3, "matches": ["a", "b"], "missing_count": 1}
    ]
    
    result = sort_recipes(recipes, "matches")
    
    assert result[0]["id"] == 2  
    assert result[1]["id"] == 3  
    assert result[2]["id"] == 1  

def test_sort_recipes_by_missing():
    """it should sort by missing count ascending"""
    recipes = [
        {"id": 1, "matches": ["a"], "missing_count": 5},
        {"id": 2, "matches": ["a", "b"], "missing_count": 1},
        {"id": 3, "matches": ["a"], "missing_count": 3}
    ]
    result = sort_recipes(recipes, "missing")
    
    assert result[0]["id"] == 2  
    assert result[1]["id"] == 3  
    assert result[2]["id"] == 1  

def test_sort_recipes_weighted_default():
    """tests weighted sorting (default)"""
    recipes = [
        {"id": 1, "matches": ["a"], "missing_count": 1},       
        {"id": 2, "matches": ["a", "b", "c"], "missing_count": 2}, 
        {"id": 3, "matches": ["a", "b"], "missing_count": 1}  
    ]
    result = sort_recipes(recipes, "weighted")
    
    assert result[0]["id"] == 2 
    assert result[1]["id"] == 3 
    assert result[2]["id"] == 1  

def test_sort_recipes_invalid_sort_uses_weighted():
    """it should default to weighted sorting on invalid sort_by"""
    recipes = [
        {"id": 1, "matches": ["a"], "missing_count": 5},
        {"id": 2, "matches": ["a", "b", "c"], "missing_count": 0}
    ]
    
    result = sort_recipes(recipes, "invalid")
    assert result[0]["id"] == 2

def test_sort_recipes_empty_list():
    result = sort_recipes([], "matches")
    assert result == []


# ---------- validate_name tests ----------
def test_validate_name_valid():
    valid, msg = validate_name("Pizza")
    assert valid is True
    assert msg == ""

def test_validate_name_empty():
    valid, msg = validate_name("")
    assert valid is False
    assert "cannot be empty" in msg

def test_validate_name_too_long():
    long_name = "a" * 101
    valid, msg = validate_name(long_name, max_length=100)
    assert valid is False
    assert "cannot exceed" in msg

def test_validate_name_exactly_max_length():
    name = "a" * 100
    valid, msg = validate_name(name, max_length=100)
    assert valid is True

def test_validate_name_whitespace_only():
    valid, msg = validate_name("   ")
    assert valid is True 


# ---------- validate_ingredients tests ----------
def test_validate_ingredients_valid():
    valid, msg = validate_ingredients(["tomato", "cheese"])
    assert valid is True
    assert msg == ""

def test_validate_ingredients_empty():
    valid, msg = validate_ingredients([])
    assert valid is False
    assert "at least one ingredient" in msg

def test_validate_ingredients_removes_duplicates():
    valid, msg = validate_ingredients(["tomato", "tomato", "cheese"])
    assert valid is True

def test_validate_ingredients_single_item():
    valid, msg = validate_ingredients(["tomato"])
    assert valid is True


# ---------- validate_instructions tests ----------
def test_validate_instructions_valid():
    valid, msg = validate_instructions("Mix all ingredients")
    assert valid is True
    assert msg == ""

def test_validate_instructions_empty():
    valid, msg = validate_instructions("")
    assert valid is False
    assert "provide instructions" in msg

def test_validate_instructions_whitespace_only():
    valid, msg = validate_instructions("   \n  \t  ")
    assert valid is False
    assert "provide instructions" in msg

def test_validate_instructions_with_content():
    valid, msg = validate_instructions("  Step 1  ")
    assert valid is True


# ---------- format_instructions tests ----------
def test_format_instructions_basic():
    """ basic formatting of instructions"""
    steps = ["Mix ingredients", "Bake for 20 minutes", "Let cool"]
    result = format_instructions(steps)
    expected = "1. Mix ingredients\n2. Bake for 20 minutes\n3. Let cool"
    assert result == expected

def test_format_instructions_removes_empty_steps():
    """it should remove empty steps"""
    steps = ["Mix ingredients", "", "Bake", "  ", "Cool"]
    result = format_instructions(steps)
    assert "Mix ingredients" in result
    assert "Bake" in result
    assert "Cool" in result
    lines = [line for line in result.split('\n') if line.strip()]
    assert len(lines) == 3

def test_format_instructions_strips_whitespace():
    """it should strip whitespace from steps"""
    steps = ["  Mix ingredients  ", "  Bake  "]
    result = format_instructions(steps)
    expected = "1. Mix ingredients\n2. Bake"
    assert result == expected

def test_format_instructions_all_empty():
    result = format_instructions(["", "  ", "\t"])
    assert result == ""


# ---------- normalize_ingredient tests ----------
def test_normalize_ingredient_plural_to_singular():
    assert normalize_ingredient("tomatoes") == "tomato"
    assert normalize_ingredient("onions") == "onion"

def test_normalize_ingredient_already_singular():
    assert normalize_ingredient("tomato") == "tomato"

def test_normalize_ingredient_case_conversion():
    assert normalize_ingredient("TOMATO") == "tomato"
    assert normalize_ingredient("ChEeSe") == "cheese"

def test_normalize_ingredient_strips_whitespace():
    assert normalize_ingredient("  tomato  ") == "tomato"

def test_normalize_ingredient_empty_string():
    assert normalize_ingredient("") == ""
    assert normalize_ingredient("   ") == ""

def test_normalize_ingredient_special_plurals():
    assert normalize_ingredient("berries") == "berry"
    assert normalize_ingredient("cherries") == "cherry"


# ---------- clean_instructions tests----------
def test_clean_instructions_html():
    """testing that HTML tags are removed"""
    html = "<p>Step 1: Mix</p><p>Step 2: Bake</p>"
    result = clean_instructions(html)
    result_str = ' '.join(result)
    assert "Mix" in result_str
    assert "Bake" in result_str
    assert "<p>" not in result_str

def test_clean_instructions_numbered_list():
    """testing numbered list parsing"""
    text = "1. Mix ingredients\n2. Bake\n3. Cool"
    result = clean_instructions(text)
    assert len(result) >= 3
    assert "Mix ingredients" in result

def test_clean_instructions_empty():
    result = clean_instructions("")
    assert result == []

def test_clean_instructions_none():
    result = clean_instructions(None)
    assert result == []

def test_clean_instructions_removes_special_chars():
    """it should remove special characters"""
    text = "Mix @#$ ingredients!!! Test"
    result = clean_instructions(text)
    assert any("Mix" in step and "ingredients" in step for step in result)


# ---------- prepare_ingredient_query tests----------
def test_prepare_ingredient_query_basic():
    """ testing basic ingredient query preparation"""
    ingredients = ["tomatoes", "onions", "garlic"]
    result = prepare_ingredient_query(ingredients)
    assert result == "tomato,onion,garlic"

def test_prepare_ingredient_query_normalizes():
    ingredients = ["TOMATOES", "  Onions  ", "Garlic"]
    result = prepare_ingredient_query(ingredients)
    assert result == "tomato,onion,garlic"

def test_prepare_ingredient_query_filters_empty():
    ingredients = ["tomato", "", "  ", "onion"]
    result = prepare_ingredient_query(ingredients)
    assert result == "tomato,onion"

def test_prepare_ingredient_query_empty_list():
    result = prepare_ingredient_query([])
    assert result == ""


# ---------- build_api_params tests ----------
def test_build_api_params_basic():
    """building API params with default limit"""
    config = {"API_KEY": "test_key"}
    params = build_api_params("tomato,cheese", 10, config)
    assert params["ingredients"] == "tomato,cheese"
    assert params["number"] == 20  # limit * 2
    assert params["apiKey"] == "test_key"

def test_build_api_params_different_limit():
    """building API params with different limit"""
    config = {"API_KEY": "key"}
    params = build_api_params("tomato", 5, config)
    
    assert params["number"] == 10


# ---------- build_recipe_dict tests ----------
def test_build_recipe_dict_basic():
    """ test building basic recipe dict """
    recipe_data = {
        "id": 123,
        "title": "Pizza",
        "usedIngredients": [{"name": "tomatoes"}],
        "missedIngredients": [{"name": "cheese"}]
    }
    
    result = build_recipe_dict(recipe_data)
    assert result["id"] == 123
    assert result["name"] == "Pizza"
    assert "tomato" in result["ingredients"]
    assert "cheese" in result["ingredients"]

def test_build_recipe_dict_with_details():
    """testing building recipe dict with details"""
    recipe_data = {
        "id": 123,
        "title": "Pizza",
        "usedIngredients": [],
        "missedIngredients": [],
        "image": "recipe.jpg"
    }
    details_data = {
        "instructions": "Bake it",
        "image": "detailed.jpg",
        "sourceUrl": "http://example.com"
    }
    result = build_recipe_dict(recipe_data, details_data)
    assert result["instructions"] == "Bake it"
    assert result["image"] == "detailed.jpg"
    assert result["sourceUrl"] == "http://example.com"

def test_build_recipe_dict_empty_image():
    """handling empty image string"""
    recipe_data = {
        "id": 123,
        "title": "Pizza",
        "usedIngredients": [],
        "missedIngredients": [],
        "image": ""
    }
    
    result = build_recipe_dict(recipe_data)
    assert result["image"] is None

def test_build_recipe_dict_no_title():
    recipe_data = {
        "id": 123,
        "usedIngredients": [],
        "missedIngredients": []
    }
    
    result = build_recipe_dict(recipe_data)
    assert result["name"] == "No name"


# ---------- build_recipe_details tests ----------
def test_build_recipe_details_complete():
    """building complete recipe details"""
    details = {
        "title": "Pasta",
        "extendedIngredients": [
            {"name": "tomatoes"},
            {"name": "basil"}
        ],
        "instructions": "<p>Boil pasta</p>",
        "image": "pasta.jpg",
        "sourceUrl": "http://example.com"
    }
    result = build_recipe_details(456, details)
    
    assert result["id"] == 456
    assert result["name"] == "Pasta"
    assert "tomato" in result["ingredients"]
    assert "basil" in result["ingredients"]
    assert isinstance(result["instructions"], list)
    assert result["image"] == "pasta.jpg"

def test_build_recipe_details_none():
    result = build_recipe_details(123, None)
    assert result is None

def test_build_recipe_details_no_image():
    """handling missing image"""
    details = {
        "title": "Test",
        "extendedIngredients": [],
        "sourceUrl": ""
    }
    
    result = build_recipe_details(123, details)
    assert result["image"] is None

def test_build_recipe_details_whitespace_image():
    """handling image with only whitespace"""
    details = {
        "title": "Test",
        "extendedIngredients": [],
        "image": "  ",
        "sourceUrl": ""
    }
    
    result = build_recipe_details(123, details)
    assert result["image"] == "" or result["image"] is None


# ----------  init_cache  tests----------
def test_init_cache_creates_caches():
    """testing that caches are created if missing"""
    mock_app = Mock()
    mock_app.recipe_cache = None
    mock_app.ingredient_cache = None
    
    if hasattr(mock_app, 'recipe_cache'):
        delattr(mock_app, 'recipe_cache')
    if hasattr(mock_app, 'ingredient_cache'):
        delattr(mock_app, 'ingredient_cache')
    
    init_cache(mock_app)
    
    assert hasattr(mock_app, 'recipe_cache')
    assert hasattr(mock_app, 'ingredient_cache')
    assert isinstance(mock_app.recipe_cache, dict)
    assert isinstance(mock_app.ingredient_cache, dict)


def test_init_cache_preserves_existing():
    """testing existing caches are preserved"""
    mock_app = Mock()
    existing_recipe_cache = {"key": "value"}
    existing_ingredient_cache = {"ing": "val"}
    mock_app.recipe_cache = existing_recipe_cache
    mock_app.ingredient_cache = existing_ingredient_cache
    init_cache(mock_app)
    
    assert mock_app.recipe_cache == existing_recipe_cache
    assert mock_app.ingredient_cache == existing_ingredient_cache