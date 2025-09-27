from flask import render_template, request, redirect, url_for, jsonify, session, abort
from .storage import (
    get_user_recipes,
    save_user_recipe,
    get_user_recipe,
    update_user_recipe,
    delete_user_recipe
)
from .api_client import search_recipes, get_recipe_details, get_ingredient_suggestions

recipe_cache = {}

def init_routes(app):
    @app.route('/')
    def home():
        return render_template("index.html")

    @app.route('/results')
    def results():
        ingredients = request.args.get("ingredients")
        sort_by = request.args.get("sort_by", "weighted")

        if ingredients:
            user_ingredients = [i.strip().lower() for i in ingredients.split(",") if i.strip()]
            key = tuple(sorted(user_ingredients))

            if key in recipe_cache:
                recipes = recipe_cache[key]
            else:
                recipes = []
                for r in search_recipes(user_ingredients):
                    matches = set(user_ingredients) & set([i.lower() for i in r.get("ingredients", [])])
                    missing_count = len(r.get("ingredients", [])) - len(matches)
                    r_copy = r.copy()
                    r_copy["matches"] = list(matches)
                    r_copy["missing_count"] = missing_count
                    recipes.append(r_copy)

                recipe_cache[key] = recipes

            sort_by = sort_by or "weighted"
            if sort_by == "matches":
                recipes.sort(key=lambda x: len(x["matches"]), reverse=True)
            elif sort_by == "missing":
                recipes.sort(key=lambda x: x["missing_count"])
            else:
                recipes.sort(key=lambda x: 2*len(x["matches"]) - x["missing_count"], reverse=True)

        else:
            recipes = []

        return render_template("results.html", recipes=recipes, ingredients=ingredients or "", sort_by=sort_by)

    @app.route('/recipe/<int:recipe_id>')
    def recipe_detail(recipe_id):
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

    @app.route('/my_recipes')
    def my_recipes():
        recipes = get_user_recipes()
        return render_template("my_recipes.html", recipes=recipes)

    @app.route('/my_recipes/new', methods=['GET', 'POST'])
    def new_recipe():
        if request.method == 'POST':
            name = request.form.get("name")
            ingredients = [i.strip() for i in request.form.get("ingredients", "").split(",") if i.strip()]
            instructions = request.form.get("instructions")
            if name and ingredients and instructions:
                # user-created recipe
                save_user_recipe(name, ingredients, instructions, source="user", api_id=None)
            return redirect(url_for('my_recipes'))
        return render_template("recipe_form.html", recipe=None)

    @app.route('/my_recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
    def edit_recipe(recipe_id):
        recipe = get_user_recipe(recipe_id)
        if not recipe:
            return "Recipe not found", 404

        # block editing if not user-created
        if recipe.get("source") != "user":
            return "Editing is not allowed for recipes saved from the API.", 403

        if request.method == 'POST':
            name = request.form.get("name")
            ingredients = [i.strip() for i in request.form.get("ingredients", "").split(",") if i.strip()]
            instructions = request.form.get("instructions")
            updated = update_user_recipe(recipe_id, name, ingredients, instructions)
            if not updated:
                # either not found or not allowed
                return "Unable to update recipe.", 400
            return redirect(url_for('my_recipes'))

        return render_template("recipe_form.html", recipe=recipe)

    @app.route('/my_recipes/<int:recipe_id>/delete', methods=['POST'])
    def delete_recipe(recipe_id):
        delete_user_recipe(recipe_id)
        return redirect(url_for('my_recipes'))

    # ---------- API Save (saving an API result into our DB) ----------
    @app.route('/save_recipe', methods=['POST'])
    def save_recipe():
        name = request.form.get("name")
        ingredients = [i.strip() for i in request.form.get("ingredients", "").split(",") if i.strip()]
        instructions = request.form.get("instructions")

        api_id_raw = request.form.get("api_id")
        api_id = int(api_id_raw) if api_id_raw and api_id_raw.isdigit() else None

        if name and ingredients and instructions:
            save_user_recipe(name, ingredients, instructions, source="api", api_id=api_id)

        return redirect(url_for('my_recipes'))


    @app.route("/ingredient_suggestions")
    def ingredient_suggestions():
        query = request.args.get("query", "").strip()
        suggestions = get_ingredient_suggestions(query)
        return jsonify(suggestions)
