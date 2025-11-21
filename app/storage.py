from typing import List, Optional, Dict, Any
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from .utils import normalize_ingredient

db = SQLAlchemy()  

# -------------------- MODELS --------------------

class Recipe(db.Model):
    __tablename__ = "my_recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    ingredients = db.Column(db.Text)
    instructions = db.Column(db.Text)
    source = db.Column(db.String, default="user")
    api_id = db.Column(db.Integer, nullable=True)


class CachedResponse(db.Model):
    __tablename__ = "cached_responses"

    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String, unique=True, nullable=False)
    response = db.Column(db.Text, nullable=False)


# -------------------- DB INIT --------------------

def init_db(app=None):
    """Initialize database tables"""
    if app:
        db.init_app(app)
        with app.app_context():
            db.create_all()
    else:
        db.create_all()


# -------------------- HELPERS --------------------

def _row_to_recipe(recipe: Recipe) -> Dict[str, Any]:
    ingredients_text = recipe.ingredients or ""
    ingredients = [i.strip() for i in ingredients_text.split(",")] if ingredients_text else []
    return {
        "id": recipe.id,
        "name": recipe.name,
        "ingredients": ingredients,
        "instructions": recipe.instructions or "",
        "source": recipe.source or "user",
        "api_id": recipe.api_id,
        "editable": recipe.source == "user"
    }


# -------------------- STORAGE FUNCTIONS --------------------

class RecipeStorage:

    @staticmethod
    def get_user_recipes() -> List[Dict[str, Any]]:
        recipes = Recipe.query.order_by(Recipe.id.desc()).all()
        return [_row_to_recipe(r) for r in recipes]

    @staticmethod
    def get_user_recipe(recipe_id: int) -> Optional[Dict[str, Any]]:
        recipe = Recipe.query.get(recipe_id)
        return _row_to_recipe(recipe) if recipe else None

    @staticmethod
    def save_user_recipe(name: str, ingredients: List[str], instructions: str,
                         source: str = "user", api_id: Optional[int] = None) -> int:
        recipe = Recipe(
            name=name,
            ingredients=",".join([i.strip() for i in ingredients if i is not None]),
            instructions=instructions,
            source=source,
            api_id=api_id
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe.id

    @staticmethod
    def update_user_recipe(recipe_id: int, name: str, ingredients: List[str], instructions: str) -> bool:
        recipe = Recipe.query.get(recipe_id)
        if not recipe or recipe.source != "user":
            return False
        recipe.name = name
        recipe.ingredients = ",".join([i.strip() for i in ingredients if i is not None])
        recipe.instructions = instructions
        db.session.commit()
        return True

    @staticmethod
    def delete_user_recipe(recipe_id: int) -> bool:
        recipe = Recipe.query.get(recipe_id)
        if not recipe or recipe.source != "user":
            return False
        db.session.delete(recipe)
        db.session.commit()
        return True


# -------------------- CACHED RESPONSES --------------------

def get_common_ingredients_from_db() -> List[str]:
    ingredients = []
    try:
        conn = db.session.bind  # get engine
        result = conn.execute("SELECT name FROM ingredients")
        ingredients = [normalize_ingredient(row[0]) for row in result.fetchall()]
    except Exception:
        pass
    return ingredients