    # ---------- FOR ROUTES.PY  ----------

def normalize_ingredients(raw_ingredients: str):
    ingredients = [i.strip().lower() for i in raw_ingredients.split(",") if i.strip()]
    return sorted(ingredients)


def build_cache_key(ingredients_list):
    return tuple(ingredients_list)


def matching_missing_for_recipe(user_ingredients, recipes):
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
    if sort_by == "matches":
        recipes.sort(key=lambda x: len(x["matches"]), reverse=True)
    elif sort_by == "missing":
        recipes.sort(key=lambda x: x["missing_count"])
    else:
        recipes.sort(key=lambda x: 2*len(x["matches"]) - x["missing_count"], reverse=True)
    return recipes


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
