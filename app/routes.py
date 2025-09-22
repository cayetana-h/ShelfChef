from flask import render_template, request, redirect, url_for
from .storage import get_user_recipes, save_user_recipe
from .api_client import search_recipes, get_recipe_details  

def init_routes(app):
    @app.route('/')
    def home():
        return render_template("index.html")

    @app.route('/results')
    def results():
        ingredients = request.args.get("ingredients", "")
        sort_by = request.args.get("sort_by", "weighted")  # default ranking
        user_ingredients = [i.strip().lower() for i in ingredients.split(",")]

        recipes = []
        for r in search_recipes(user_ingredients):
            matches = set(user_ingredients) & set([i.lower() for i in r.get("ingredients", [])])
            missing_count = len(r.get("ingredients", [])) - len(matches)
            r_copy = r.copy()
            r_copy["matches"] = list(matches)
            r_copy["missing_count"] = missing_count
            recipes.append(r_copy)

        # ranking options
        if sort_by == "matches":
            recipes.sort(key=lambda x: len(x["matches"]), reverse=True)
        elif sort_by == "missing":
            recipes.sort(key=lambda x: x["missing_count"])
        else:  # weighted (default)
            recipes.sort(key=lambda x: 2*len(x["matches"]) - x["missing_count"], reverse=True)

        return render_template("results.html", recipes=recipes, ingredients=ingredients, sort_by=sort_by)

    @app.route('/recipe/<int:recipe_id>')
    def recipe_detail(recipe_id):
        """Showing full recipe information from API"""
        recipe = get_recipe_details(recipe_id)
        if not recipe:
            return "Recipe not found", 404
        return render_template("recipe_detail.html", recipe=recipe)

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
