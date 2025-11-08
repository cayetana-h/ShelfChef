import requests
import json
from flask import current_app
from .utils import( 
    build_recipe_dict, normalize_ingredient, clean_instructions,prepare_ingredient_query, 
    get_recipes_from_cache, build_api_params, fetch_recipes_from_api, save_recipes_to_cache, 
    get_cached_response, save_cached_response, fetch_recipe_details, fetch_ingredient_suggestions_from_api,
    get_ingredient_suggestions_from_cache)
from .storage import get_common_ingredients_from_db

from dotenv import load_dotenv
load_dotenv()


def search_recipes(user_ingredients, limit=10, config=None):
    """
    searching recipes based on user-provided ingredients
    first checking local cache, then falling back to API if needed
    """
    config = config or current_app.config
    ingredients_str = prepare_ingredient_query(user_ingredients)

    recipes = get_recipes_from_cache(ingredients_str)
    if recipes:
        return recipes

    recipes = fetch_recipes_from_api(ingredients_str, limit, config)
    
    recipes.sort(key=lambda r: r["missing_ingredients"])
    final_recipes = recipes[:limit]

    save_recipes_to_cache(ingredients_str, final_recipes)

    return final_recipes


def get_recipe_details(recipe_id, config=None, requester=requests):
    """
    fetching full details for a single recipe by ID 
    """
    config = config or current_app.config
    details = fetch_recipe_details(recipe_id, config, requester)

    if not details:
        print(f"Failed to fetch recipe {recipe_id}")
        return None
    
    image = details.get("image")
    if image:
        image = image.strip()
    if not image:
        image = None
    return {
        "id": recipe_id,
        "name": details.get("title", "No name"),
        "ingredients": [normalize_ingredient(ing["name"]) for ing in details.get("extendedIngredients", [])],
        "instructions": clean_instructions(details.get("instructions", "")),  
        "image": image,
        "sourceUrl": details.get("sourceUrl", "")
    }


def get_ingredient_suggestions(query, config=None):
    """
    fetching ingredient suggestions based on user input
    using local db cache first, then falling back to API if needed
    """
    config = config or current_app.config
    query = normalize_ingredient(query)

    if query == "":
        return get_common_ingredients_from_db()

    if query in current_app.ingredient_cache:
        return current_app.ingredient_cache[query]

    cached = get_ingredient_suggestions_from_cache(query, current_app.ingredient_cache)
    if cached:
        return cached
    
    suggestions = [s for s in get_common_ingredients_from_db() if s.startswith(query)]

    if not suggestions:
        suggestions = fetch_ingredient_suggestions_from_api(query, config)
        save_cached_response(f"ingredient_suggestions:{query}", json.dumps(suggestions))

    return suggestions
