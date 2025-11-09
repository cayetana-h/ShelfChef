from flask import render_template, request, redirect, url_for, jsonify, flash, current_app, Blueprint
from .api_client import get_ingredient_suggestions
from .storage import RecipeStorage

from .utils import (
    normalize_ingredients,get_processed_recipes, 
    fetch_recipe_or_404, process_new_recipe_form, extract_api_recipe_form
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
        recipes = get_processed_recipes(user_ingredients, sort_by, current_app.recipe_cache)
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
    try:
        recipe = fetch_recipe_or_404(recipe_id)
    except ValueError:
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
    recipes = RecipeStorage.get_user_recipes()
    return render_template("my_recipes.html", recipes=recipes)

@bp.route('/my_recipes/new', methods=['GET', 'POST'])
def new_recipe():
    """
    displaying the new recipe form and saving a new user recipe (validation)
    """
    if request.method == "POST":
        valid, msg, ingredients, instructions = process_new_recipe_form(request.form)
        if not valid:
            flash(msg, "error")
            return render_template("recipe_form.html", recipe=None)

        RecipeStorage.save_user_recipe(request.form.get("name", "").title().strip(), ingredients, instructions, source="user", api_id=None)

        flash("Recipe added successfully!", "success")
        return redirect(url_for("main.my_recipes"))

    return render_template("recipe_form.html", recipe=None)


@bp.route('/my_recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """
    displaying the edit form and updating a user's recipe (valdiation)
    """
    recipe = RecipeStorage.get_user_recipe(recipe_id)
    if not recipe:
        return "Recipe not found", 404

    if recipe.get("source") != "user":
        return "Editing is not allowed for recipes saved from the API.", 403

    if request.method == "POST":
        valid, msg, ingredients, instructions = process_new_recipe_form(request.form)

        name = request.form.get("name", "").title().strip()

        if not valid:
            flash(msg, "error")
            return render_template("recipe_form.html", recipe=recipe)

        updated = RecipeStorage.update_user_recipe(recipe_id, name, ingredients, instructions)
        if not updated:
            flash("Unable to update recipe.", "error")
            return render_template("recipe_form.html", recipe=recipe)

        return redirect(url_for("main.my_recipes"))
    return render_template("recipe_form.html", recipe=recipe)

@bp.route('/my_recipes/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    RecipeStorage.delete_user_recipe(recipe_id)
    return redirect(url_for('main.my_recipes'))

# ---------- API Save (saving an API result into DB) ----------
@bp.route('/save_recipe', methods=['POST'])
def save_recipe():
    """saving a recipe coming from the API to my recipes"""
    valid, msg, name, ingredients, instructions, api_id = extract_api_recipe_form(request.form)

    if not valid:
        flash(msg, "error")
        return redirect(request.referrer or url_for("home"))

    RecipeStorage.save_user_recipe(name, ingredients, instructions, source="api", api_id=api_id)
    return redirect(url_for("main.my_recipes"))


@bp.route("/ingredient_suggestions")
def ingredient_suggestions():
    """
    provides ingredient suggestions for autocomplete as JSON (autocomplete)
    """
    query = request.args.get("query", "").strip()
    suggestions = get_ingredient_suggestions(query)
    return jsonify(suggestions)