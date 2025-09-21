from flask import render_template, request, redirect, url_for
from .storage import get_user_recipes, save_user_recipe

# Dummy recipes for search results
RECIPES = [
    {"name": "Pasta", "ingredients": ["pasta", "tomato", "cheese"], "instructions": "Boil pasta. Add sauce."},
    {"name": "Salad", "ingredients": ["lettuce", "tomato", "cucumber"], "instructions": "Mix all ingredients."},
    {"name": "Omelette", "ingredients": ["eggs", "cheese", "milk"], "instructions": "Beat eggs, cook in pan, add cheese."}
]

def init_routes(app):
    @app.route('/')
    def home():
        return render_template("index.html")

    @app.route('/results')
    def results():
        ingredients = request.args.get("ingredients", "")
        user_ingredients = [i.strip().lower() for i in ingredients.split(",")]

        matching_recipes = []
        for r in RECIPES:
            matches = set(user_ingredients) & set([i.lower() for i in r["ingredients"]])
            if matches:
                r_copy = r.copy()
                r_copy["matches"] = list(matches)
                matching_recipes.append(r_copy)

        return render_template("results.html", recipes=matching_recipes, ingredients=ingredients)

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
