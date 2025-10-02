

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


    # ---------- API_CLIENT.PY----------

import inflect
p = inflect.engine()

def normalize_ingredient(ingredient: str) -> str:
    """ normalizing ingredient names for consistency"""
    ing = ingredient.strip().lower()
    ing = ''.join(c for c in ing if c.isalpha() or c.isspace()) 
    ing = p.singular_noun(ing) or ing 
    return ing


def build_recipe_dict(recipe_data, details_data=None):
    """
    building a consistent recipe dictionary from API data
    """
    ingredients = [normalize_ingredient(i["name"]) 
                   for i in recipe_data.get("usedIngredients", []) + recipe_data.get("missedIngredients", [])]

    recipe_dict = {
        "id": recipe_data.get("id"),
        "name": recipe_data.get("title", "No name"),
        "ingredients": ingredients,
        "instructions": details_data.get("instructions", "") if details_data else "",
        "image": details_data.get("image", "") if details_data else "",
        "missing_ingredients": len(recipe_data.get("missedIngredients", [])),
        "sourceUrl": details_data.get("sourceUrl", "") if details_data else ""
    }

    return recipe_dict


