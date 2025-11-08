# ---------- CACHE HELPERS  ----------
import json
from .db_utils import db_connection
from typing import List, Optional, Dict, Any

def get_cached_response(query: str) -> Optional[str]:
    """returns cached JSON string for a query if it exists"""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT response FROM cached_responses WHERE query = ?", (query,))
        row = c.fetchone()
    return row["response"] if row else None

def save_cached_response(query: str, response: str) -> None:
    """saves or updates cache for a query"""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO cached_responses (query, response) VALUES (?, ?)
            ON CONFLICT(query) DO UPDATE SET response=excluded.response
        """, (query, response))
        conn.commit()

    # ---------- FOR ROUTES.PY  ----------

def normalize_ingredients(raw_ingredients: str):
    """"normalizing user input ingredients"""
    ingredients = [i.strip().lower() for i in raw_ingredients.split(",") if i.strip()]
    return sorted(ingredients)


def build_cache_key(ingredients_list):
    """ creating a hashable cache key from user ingredients to store/retrieve search results"""
    return tuple(ingredients_list)


def matching_missing_for_recipe(user_ingredients, recipes):
    """ adding matches and missing_count to each recipe dict"""
    enriched = []
    for r in recipes:
        matches = set(user_ingredients) & set([i.lower() for i in r.get("ingredients", [])])
        missing_count = len(r.get("ingredients", [])) - len(matches)
        r_copy = r.copy()
        r_copy["matches"] = list(matches)
        r_copy["missing_count"] = missing_count
        enriched.append(r_copy)
    return enriched

def sort_recipes(recipes, sort_by="weighted"):
    """ sorting recipes based on user preference"""
    if sort_by == "matches":
        recipes.sort(key=lambda x: len(x["matches"]), reverse=True)
    elif sort_by == "missing":
        recipes.sort(key=lambda x: x["missing_count"])
    else:
        recipes.sort(key=lambda x: 2*len(x["matches"]) - x["missing_count"], reverse=True) # default 
    return recipes

def validate_recipe_form(name: str, raw_ingredients: str, steps: list):
    """
    validation for recipe form inputs
    """
    ingredients = normalize_ingredients(raw_ingredients)
    instructions = format_instructions(steps)

    valid, msg = validate_name(name)
    if not valid:
        return False, msg, ingredients, instructions

    valid, msg = validate_ingredients(ingredients)
    if not valid:
        return False, msg, ingredients, instructions

    valid, msg = validate_instructions(instructions)
    if not valid:
        return False, msg, ingredients, instructions

    return True, "", ingredients, instructions



    # ---------- MAINLY FOR MY RECIPES CRUD IN REOUTES.PY----------

def validate_name(name: str, max_length=100):
    """checking if the recipe name is  not too long or null"""
    if not name:
        return False, "Recipe name cannot be empty."
    if len(name) > max_length:
        return False, f"Recipe name cannot exceed {max_length} characters."
    return True, ""

def validate_ingredients(ingredients: list):
    """checking there is at least one ingredient """
    ingredients = list(dict.fromkeys(ingredients)) 
    if not ingredients:
        return False, "Please provide at least one ingredient.", []
    return True, ""

def validate_instructions(instructions: str):
    """checking instructions are not null"""
    if not instructions.strip():
        return False, "Please provide instructions."
    return True, ""

def format_instructions(steps: list):
    """ transforming a list of steps into a numbered string and removing empty steps"""
    return "\n".join(f"{i+1}. {step.strip()}" for i, step in enumerate(steps) if step.strip())


    # ---------- FOR API_CLIENT.PY----------

import inflect
import re
from bs4 import BeautifulSoup

p = inflect.engine()

def normalize_ingredient(ingredient: str) -> str:
    """ normalizing ingredient names for consistency"""
    ing = ingredient.strip().lower()
    if not ing:
        return ""
    ing = p.singular_noun(ing) or ing
    return ing


def build_recipe_dict(recipe_data, details_data=None):
    """ building a consistent recipe dictionary from API data """
    ingredients = [
        normalize_ingredient(i["name"])
        for i in recipe_data.get("usedIngredients", []) + recipe_data.get("missedIngredients", [])
    ]
    
    image = None
    if details_data and details_data.get("image"):
        image = details_data.get("image")
        if isinstance(image, str):
            image = image.strip()
    elif recipe_data.get("image"):
        image = recipe_data.get("image")
        if isinstance(image, str):
            image = image.strip()
    
    if not image or image == "":
        image = None
    
    recipe_dict = {
        "id": recipe_data.get("id"),
        "name": recipe_data.get("title", "No name"),
        "ingredients": ingredients,
        "instructions": details_data.get("instructions", "") if details_data else "",
        "image": image,
        "missing_ingredients": len(recipe_data.get("missedIngredients", [])),
        "sourceUrl": details_data.get("sourceUrl", "") if details_data else ""
    }
    
    return recipe_dict


def clean_instructions(raw_instructions: str):
    """ cleaning and splitting raw HTML instructions"""
    if not raw_instructions:
        return []

    text = BeautifulSoup(raw_instructions, "html.parser").get_text()
    steps = re.split(r'(?:\d+\.\s*|\n+)', text)
    steps = [re.sub(r'[^\w\s,.()/-]', '', step).strip() for step in steps if step.strip()]

    return steps

def prepare_ingredient_query(user_ingredients):
    """ preparing a normalized, comma-separated ingredient string for API queries"""
    normalized = [normalize_ingredient(i) for i in user_ingredients if i.strip()]
    return ",".join(normalized)

import json
def get_recipes_from_cache(ingredients_str):
    """ retrieving cached recipes for a given ingredient query"""
    cached = get_cached_response(ingredients_str)
    if not cached:
        return None
    try:
        return json.loads(cached)
    except Exception:
        return None

def build_api_params(ingredients_str, limit, config):
    """ building parameters for API request"""
    return {"ingredients": ingredients_str, "number": limit*2, "apiKey": config["API_KEY"]}

import requests
def fetch_recipes_from_api(ingredients_str, limit, config, requester=requests):
    """ fetching recipes from external API"""
    response = requester.get(config["API_URL"], params={"ingredients": ingredients_str, "number": limit*2, "apiKey": config["API_KEY"]})
    if response.status_code != 200:
        return []

    recipes_data = response.json()
    recipes = []
    for recipe in recipes_data:
        recipe_id = recipe["id"]
        details_resp = requester.get(config["RECIPE_DETAILS_URL"].format(id=recipe_id), params={"apiKey": config["API_KEY"]})
        details = details_resp.json() if details_resp.status_code == 200 else None
        recipes.append(build_recipe_dict(recipe, details))
    return recipes

def save_recipes_to_cache(ingredients_str, recipes):
    """ saving fetched recipes to cache"""
    save_cached_response(ingredients_str, json.dumps(recipes))

def fetch_recipe_details(recipe_id, config, requester=requests):
    """
    fetching full details for a single recipe by ID
    """
    response = requester.get(
        config["RECIPE_DETAILS_URL"].format(id=recipe_id),
        params={"apiKey": config["API_KEY"]}
    )
    if response.status_code != 200:
        return None
    return response.json()

def build_recipe_details(recipe_id, details):
    """ building recipe details dict from API response"""
    if not details:
        return None

    image = details.get("image")
    if image:
        image = image.strip()
    else:
        image = None

    return {
        "id": recipe_id,
        "name": details.get("title", "No name"),
        "ingredients": [normalize_ingredient(ing["name"]) for ing in details.get("extendedIngredients", [])],
        "instructions": clean_instructions(details.get("instructions", "")),
        "image": image,
        "sourceUrl": details.get("sourceUrl", "")
    }

def fetch_ingredient_suggestions_from_api(query, config, requester=requests):
    """
    fetching ingredient suggestions based on user input from external API
    """
    try:
        response = requester.get(
            config["INGREDIENT_AUTOCOMPLETE_URL"],
            params={"query": query, "number": 10, "apiKey": config["API_KEY"]}
        )
        if response.status_code == 200:
            return [normalize_ingredient(item["name"]) for item in response.json()]
    except Exception as e:
        print(f"Error fetching ingredient suggestions from API: {e}")
    return []

def get_ingredient_suggestions_from_cache(query, ingredient_cache):
    """ retrieving ingredient suggestions from in-memory cache"""
    return ingredient_cache.get(query)

def save_ingredient_suggestions_to_cache(query, suggestions, ingredient_cache):
    """ saving ingredient suggestions to in-memory cache"""
    ingredient_cache[query] = suggestions


    # ----------__INIT__.PY----------

def init_cache(app):
    """ initializing in-memory caches for recipes and ingredients """
    caches = {
        "recipe_cache": {},
        "ingredient_cache": {}
    }

    for name, cache in caches.items():
        if not hasattr(app, name):
            setattr(app, name, cache)
