import requests
import sqlite3
from .utils import build_recipe_dict, normalize_ingredient

API_KEY = "3f522310e0834471886574d3cef664c5"  
API_URL = "https://api.spoonacular.com/recipes/findByIngredients"
RECIPE_DETAILS_URL = "https://api.spoonacular.com/recipes/{id}/information"
INGREDIENT_AUTOCOMPLETE_URL = "https://api.spoonacular.com/food/ingredients/autocomplete"

ingredient_cache = {}


from app.utils import build_recipe_dict

def search_recipes(user_ingredients, limit=10):
    """
    searching recipes on spoonacular based on user ingredients
    retrieveing twice the display limit to find best matches and not run out of api calls
    """
    normalized_ingredients = [normalize_ingredient(i) for i in user_ingredients if i.strip()]
    ingredients_str = ",".join(normalized_ingredients)
    params = {"ingredients": ingredients_str, "number": limit * 2, "apiKey": API_KEY}  

    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        print(f"API error: {response.status_code}")
        return []

    recipes_data = response.json()
    recipes = []

    for recipe in recipes_data:
        recipe_id = recipe["id"]
        details_response = requests.get(RECIPE_DETAILS_URL.format(id=recipe_id), params={"apiKey": API_KEY})
        details = details_response.json() if details_response.status_code == 200 else None
        recipes.append(build_recipe_dict(recipe, details))

    recipes.sort(key=lambda r: r["missing_ingredients"])

    return recipes[:limit]



def get_recipe_details(recipe_id):
    """
    Fetching full details for a single recipe by ID.
    """
    response = requests.get(RECIPE_DETAILS_URL.format(id=recipe_id), params={"apiKey": API_KEY})
    if response.status_code == 200:
        details = response.json()
        return {
            "id": recipe_id,
            "name": details.get("title", "No name"),
            "ingredients": [normalize_ingredient(ingredient["name"]) for ingredient in details.get("extendedIngredients", [])],
            "instructions": details.get("instructions", ""),
            "image": details.get("image", ""),
            "sourceUrl": details.get("sourceUrl", "")
        }
    else:
        print(f"Failed to fetch recipe {recipe_id}, status: {response.status_code}")
        return None

def get_common_ingredients_from_db():
    """Fetch common ingredients stored in the SQLite database."""
    conn = sqlite3.connect("recipes.db")
    c = conn.cursor()
    c.execute("SELECT name FROM ingredients")  
    rows = c.fetchall()
    conn.close()
    return [normalize_ingredient(row[0]) for row in rows]

def get_ingredient_suggestions(query):
    """
    Returns ingredient suggestions from DB (if query empty),
    in-memory cache, or Spoonacular autocomplete if nothing else matches.
    """
    query = normalize_ingredient(query)

    if query == "":
        return get_common_ingredients_from_db()

    if query in ingredient_cache:
        return ingredient_cache[query]

    conn = sqlite3.connect("recipes.db")
    c = conn.cursor()
    c.execute("SELECT name FROM ingredients WHERE name LIKE ?", (f"{query}%",))
    rows = c.fetchall()
    conn.close()

    suggestions = [normalize_ingredient(row[0]) for row in rows]

    if not suggestions:
        try:
            response = requests.get(
                INGREDIENT_AUTOCOMPLETE_URL,
                params={"query": query, "number": 10, "apiKey": API_KEY}
            )
            if response.status_code == 200:
                suggestions = [normalize_ingredient(item["name"]) for item in response.json()]
                ingredient_cache[query] = suggestions
        except Exception as e:
            print(f"Error fetching ingredient suggestions from API: {e}")
            suggestions = []

    return suggestions
