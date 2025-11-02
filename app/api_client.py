import requests
import json
from flask import current_app
from .utils import build_recipe_dict, normalize_ingredient, clean_instructions
from .storage import get_cached_response, save_cached_response, get_common_ingredients_from_db

from dotenv import load_dotenv
load_dotenv()


def search_recipes(user_ingredients, limit=10):
    """
    searching recipes based on user-provided ingredients
    first checking local cache, then falling back to API if needed
    """
    normalized_ingredients = [normalize_ingredient(i) for i in user_ingredients if i.strip()]
    ingredients_str = ",".join(normalized_ingredients)

    cached = get_cached_response(ingredients_str)
    if cached:
        try:
            return json.loads(cached)
        except Exception as e:
            print(f"Cache decode error: {e}, falling back to API...")

    params = {"ingredients": ingredients_str, "number": limit * 2, "apiKey": current_app.config["API_KEY"]}  
    
    response = requests.get(current_app.config["API_URL"], params=params)
    if response.status_code != 200:
        print(f"API error: {response.status_code}")
        return []

    recipes_data = response.json()
    recipes = []

    for recipe in recipes_data:
        recipe_id = recipe["id"]
        details_response = requests.get(current_app.config["RECIPE_DETAILS_URL"].format(id=recipe_id), params={"apiKey": current_app.config["API_KEY"]})
        details = details_response.json() if details_response.status_code == 200 else None
        recipes.append(build_recipe_dict(recipe, details))

    recipes.sort(key=lambda r: r["missing_ingredients"])
    final_recipes = recipes[:limit]

    save_cached_response(ingredients_str, json.dumps(final_recipes))

    return final_recipes


def get_recipe_details(recipe_id):
    """
    fetching full details for a single recipe by ID 
    """
    response = requests.get(current_app.config["RECIPE_DETAILS_URL"].format(id=recipe_id), params={"apiKey": current_app.config["API_KEY"]})
    
    if response.status_code == 200:
        details = response.json()
        image = details.get("image", "")
        if image:
            image = image.strip()
        if not image:
            image = None
        return {
            "id": recipe_id,
            "name": details.get("title", "No name"),
            "ingredients": [normalize_ingredient(ing["name"]) for ing in details.get("extendedIngredients", [])],
            "instructions": clean_instructions(details.get("instructions", "")),  
            "image": details.get("image") if details and details.get("image") else None,
            "sourceUrl": details.get("sourceUrl", "")
        }
    else:
        print(f"Failed to fetch recipe {recipe_id}, status: {response.status_code}")
        return None


def get_ingredient_suggestions(query):
    """
    fetching ingredient suggestions based on user input
    using local db cache first, then falling back to API if needed
    """
    query = normalize_ingredient(query)

    if query == "":
        return get_common_ingredients_from_db()

    if query in current_app.ingredient_cache:
        return current_app.ingredient_cache[query]

    suggestions = get_common_ingredients_from_db()
    suggestions = [s for s in suggestions if s.startswith(query)]

    if not suggestions:
        try:
            response = requests.get(
                current_app.config["INGREDIENT_AUTOCOMPLETE_URL"],
                params={"query": query, "number": 10, "apiKey": current_app.config["API_KEY"]}
            )
            if response.status_code == 200:
                suggestions = [normalize_ingredient(item["name"]) for item in response.json()]
                current_app.ingredient_cache[query] = suggestions
        except Exception as e:
            print(f"Error fetching ingredient suggestions from API: {e}")
            suggestions = []

    return suggestions
