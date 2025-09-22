import requests

API_KEY = "3f522310e0834471886574d3cef664c5"  
API_URL = "https://api.spoonacular.com/recipes/findByIngredients"
RECIPE_DETAILS_URL = "https://api.spoonacular.com/recipes/{id}/information"

def search_recipes(user_ingredients):
    """
    Search recipes using Spoonacular's findByIngredients endpoint.
    Returns a list of recipes with name, ingredients, instructions, 
    missing ingredients count, and source URL.
    """
    ingredients_str = ",".join(user_ingredients)
    params = {
        "ingredients": ingredients_str,
        "number": 10, 
        "apiKey": API_KEY
    }

    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        print(f"API error: {response.status_code}")
        return []

    recipes_data = response.json()
    recipes = []

    for recipe in recipes_data:
        recipe_id = recipe["id"]

        details_response = requests.get(RECIPE_DETAILS_URL.format(id=recipe_id), params={"apiKey": API_KEY})
        if details_response.status_code == 200:
            details = details_response.json()
            recipes.append({
                "id": recipe_id,
                "name": recipe.get("title", "No name"),
                "ingredients": [i["name"] for i in recipe.get("usedIngredients", []) + recipe.get("missedIngredients", [])],
                "instructions": details.get("instructions", ""),
                "image": details.get("image", ""),
                "missing_ingredients": len(recipe.get("missedIngredients", [])),
                "sourceUrl": details.get("sourceUrl", "")
            })
        else:
            recipes.append({
                "id": recipe_id,
                "name": recipe.get("title", "No name"),
                "ingredients": [i["name"] for i in recipe.get("usedIngredients", []) + recipe.get("missedIngredients", [])],
                "instructions": "",
                "image": "",
                "missing_ingredients": len(recipe.get("missedIngredients", [])),
                "sourceUrl": ""
            })

    return recipes

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
            "ingredients": [ingredient["name"] for ingredient in details.get("extendedIngredients", [])],
            "instructions": details.get("instructions", ""),
            "image": details.get("image", ""),
            "sourceUrl": details.get("sourceUrl", "")
        }
    else:
        print(f"Failed to fetch recipe {recipe_id}, status: {response.status_code}")
        return None
