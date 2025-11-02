from flask import render_template, request, redirect, url_for, jsonify, flash, current_app, Blueprint
from .storage import (
    get_user_recipes, save_user_recipe, get_user_recipe,
    update_user_recipe, delete_user_recipe
    )
from .api_client import search_recipes, get_recipe_details, get_ingredient_suggestions
from .utils import (
    normalize_ingredients, build_cache_key, matching_missing_for_recipe, 
    sort_recipes, validate_name, validate_ingredients, validate_instructions, 
    format_instructions, validate_recipe_form
    )

bp = Blueprint("main", __name__)


@bp.route('/')
def home():
    return render_template("index.html")

@bp.route('/results')
def results():
    """ 
    displays recipe search results based on user ingredients and sort preference
    """
    raw_input = request.args.get("ingredients", "")
    sort_by = request.args.get("sort_by", "weighted")

    if raw_input:
        user_ingredients = normalize_ingredients(raw_input)
        key = build_cache_key(user_ingredients)

        if key in current_app.recipe_cache:
            recipes = current_app.recipe_cache[key]
        else:
            api_results = search_recipes(user_ingredients)
            recipes = matching_missing_for_recipe(user_ingredients, api_results)
            current_app.recipe_cache[key] = recipes

        recipes = sort_recipes(recipes, sort_by)
    else:
        recipes = []

    return render_template(
        "results.html",
        recipes=recipes,
        ingredients=raw_input,
        sort_by=sort_by
    )

@bp.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """
    fetches and displays recipe steps about a specific recipe
    """
    recipe = get_recipe_details(recipe_id)
    if not recipe:
        return "Recipe not found", 404

    ingredients = request.args.get("ingredients", "")
    sort_by = request.args.get("sort_by", "weighted")

    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        ingredients=ingredients,
        sort_by=sort_by
    )

# ---------- MY RECIPES CRUD ----------

@bp.route('/my_recipes')
def my_recipes():
    recipes = get_user_recipes()
    return render_template("my_recipes.html", recipes=recipes)

@bp.route('/my_recipes/new', methods=['GET', 'POST'])
def new_recipe():
    """
    handles both displaying the form and processing form submissions for new recipes
    """
    if request.method == "POST":
        name = request.form.get("name", "").title().strip()
        raw_ingredients = request.form.get("ingredients", "")
        steps = request.form.getlist("instructions[]")

        valid, msg, ingredients, instructions = validate_recipe_form(name, raw_ingredients, steps)
        if not valid:
            flash(msg, "error")
            return render_template("recipe_form.html", recipe=None)

        save_user_recipe(name, ingredients, instructions, source="user", api_id=None)
        return redirect(url_for("my_recipes"))

    return render_template("recipe_form.html", recipe=None)


@bp.route('/my_recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """
    displaying the edit form and updating a user's recipe (valdiation)
    """
    recipe = get_user_recipe(recipe_id)
    if not recipe:
        return "Recipe not found", 404

    if recipe.get("source") != "user":
        return "Editing is not allowed for recipes saved from the API.", 403

    if request.method == "POST":
        name = request.form.get("name", "").title().strip()
        raw_ingredients = request.form.get("ingredients", "")
        steps = request.form.getlist("instructions[]")

        valid, msg, ingredients, instructions = validate_recipe_form(name, raw_ingredients, steps)
        if not valid:
            flash(msg, "error")
            return render_template("recipe_form.html", recipe=recipe)

        updated = update_user_recipe(recipe_id, name, ingredients, instructions)
        if not updated:
            flash("Unable to update recipe.", "error")
            return render_template("recipe_form.html", recipe=recipe)

        return redirect(url_for("my_recipes"))


    recipe_steps = recipe.get("instructions", "").split("\n")
    return render_template("recipe_form.html", recipe=recipe, recipe_steps=recipe_steps)

@bp.route('/my_recipes/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    delete_user_recipe(recipe_id)
    return redirect(url_for('my_recipes'))

# ---------- API Save (saving an API result into DB) ----------
@bp.route('/save_recipe', methods=['POST'])
def save_recipe():
    """saving a recipe coming from the API to my recipes"""
    name = request.form.get("name", "").title().strip()
    raw_ingredients = request.form.get("ingredients", "")
    steps = request.form.get("instructions", "").split("\n")
    api_id_raw = request.form.get("api_id")
    api_id = int(api_id_raw) if api_id_raw and api_id_raw.isdigit() else None


    valid, msg, ingredients, instructions = validate_recipe_form(name, raw_ingredients, steps)
    if not valid:
        flash(msg, "error")
        return redirect(request.referrer or url_for("home"))

    save_user_recipe(name, ingredients, instructions, source="api", api_id=api_id)
    return redirect(url_for("my_recipes"))


@bp.route("/ingredient_suggestions")
def ingredient_suggestions():
    """
    provides ingredient suggestions for autocomplete as JSON (autocomplete)
    """
    query = request.args.get("query", "").strip()
    suggestions = get_ingredient_suggestions(query)
    return jsonify(suggestions)