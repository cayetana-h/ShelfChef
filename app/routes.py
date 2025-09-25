from flask import render_template, request, redirect, url_for, jsonify, session  # added session
from .storage import get_user_recipes, save_user_recipe
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

            # check cache first
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

                # store in cache
                recipe_cache[key] = recipes

            # ranking
            sort_by = sort_by or "weighted"
            if sort_by == "matches":
                recipes.sort(key=lambda x: len(x["matches"]), reverse=True)
            elif sort_by == "missing":
                recipes.sort(key=lambda x: x["missing_count"])
            else:
                recipes.sort(key=lambda x: 2*len(x["matches"]) - x["missing_count"], reverse=True)

        else:
            # fallback if no ingredients param
            recipes = []

        return render_template("results.html", recipes=recipes, ingredients=ingredients or "", sort_by=sort_by)


    @app.route('/recipe/<int:recipe_id>')
    def recipe_detail(recipe_id):
        recipe = get_recipe_details(recipe_id)
        if not recipe:
            return "Recipe not found", 404

        # pass original search ingredients and sort_by to template
        ingredients = request.args.get("ingredients", "")  # original search ingredients
        sort_by = request.args.get("sort_by", "weighted")

        return render_template(
            "recipe_detail.html",
            recipe=recipe,
            ingredients=ingredients,  # this is key
            sort_by=sort_by
        )


    @app.route('/my_recipes')
    def my_recipes():
        recipes = get_user_recipes()
        return render_template("my_recipes.html", recipes=recipes)

    @app.route('/save_recipe', methods=['POST'])
    def save_recipe():
        name = request.form.get("name")
        ingredients = request.form.get("ingredients", "").split(",")
        instructions = request.form.get("instructions")
        if name and ingredients and instructions:
            save_user_recipe(name, ingredients, instructions)
        return redirect(url_for('my_recipes'))

    @app.route("/ingredient_suggestions")
    def ingredient_suggestions():
        query = request.args.get("query", "").strip()
        suggestions = get_ingredient_suggestions(query)
        return jsonify(suggestions)
