import sqlite3
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from flask import current_app
from .utils import normalize_ingredient
from .db_utils import db_connection

class DatabaseInitializer:
    @staticmethod
    def ensure_db():
        """ensuring the database and tables exist, with necessary schema"""
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS my_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ingredients TEXT,
                    instructions TEXT,
                    source TEXT DEFAULT 'user',
                    api_id INTEGER
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS cached_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT UNIQUE NOT NULL,
                    response TEXT NOT NULL
                )
            """)
        
            DatabaseInitializer.add_missing_columns(conn)
            conn.commit()
    
    @staticmethod
    def add_missing_columns(c):
        cols = [r["name"] for r in c.execute("PRAGMA table_info(my_recipes)").fetchall()]
        if "source" not in cols:
            c.execute("ALTER TABLE my_recipes ADD COLUMN source TEXT DEFAULT 'user'")
        if "api_id" not in cols:
            c.execute("ALTER TABLE my_recipes ADD COLUMN api_id INTEGER")


def _row_to_recipe(row: sqlite3.Row) -> Dict[str, Any]:
    """convertng a DB row to a recipe dict"""
    ingredients_text = row["ingredients"] or ""
    ingredients = [i.strip() for i in ingredients_text.split(",")] if ingredients_text else []
    source = row["source"] if "source" in row.keys() else "user"
    api_id = row["api_id"] if "api_id" in row.keys() else None
    return {
        "id": row["id"],
        "name": row["name"],
        "ingredients": ingredients,
        "instructions": row["instructions"] or "",
        "source": source,
        "api_id": api_id,
        "editable": True if source == "user" else False
    }

class RecipeStorage:
    @staticmethod
    def get_user_recipes() -> List[Dict[str, Any]]:
        """retrieving all stored recipes (both user-created and saved-from-API)."""
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, ingredients, instructions, source, api_id FROM my_recipes ORDER BY id DESC")
            return [_row_to_recipe(r) for r in c.fetchall()]

    @staticmethod
    def get_user_recipe(recipe_id: int) -> Optional[Dict[str, Any]]:
        """retrieves a single recipe by ID."""
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, ingredients, instructions, source, api_id FROM my_recipes WHERE id = ?", (recipe_id,))
            row = c.fetchone()
            return _row_to_recipe(row) if row else None
    
    @staticmethod
    def save_user_recipe(name: str, ingredients: List[str], instructions: str, source: str = "user", api_id: Optional[int] = None) -> int:
        """
        saves a new recipe to the db + returns new recipe ID
        """
        with db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO my_recipes (name, ingredients, instructions, source, api_id) VALUES (?, ?, ?, ?, ?)",
                (name, ",".join([i.strip() for i in ingredients if i is not None]), instructions, source, api_id)
            )
            conn.commit()
            return c.lastrowid

    @staticmethod
    def update_user_recipe(recipe_id: int, name: str, ingredients: List[str], instructions: str) -> bool:
        """
        updates an existing user-created recipe
        """
        existing = RecipeStorage.get_user_recipe(recipe_id)
        if not existing or existing.get("source") != "user":
            return False

        with db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE my_recipes SET name = ?, ingredients = ?, instructions = ? WHERE id = ?",
                (name, ",".join([i.strip() for i in ingredients if i is not None]), instructions, recipe_id)
            )
            conn.commit()
            return c.rowcount > 0

    @staticmethod
    def delete_user_recipe(recipe_id: int) -> bool:
        """deletes a user-created recipe by ID"""
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM my_recipes WHERE id = ?", (recipe_id,))
            conn.commit()
            return c.rowcount > 0

def get_common_ingredients_from_db():
    """fetiching common ingredients stored in the db"""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM ingredients")  
        return [normalize_ingredient(row[0]) for row in c.fetchall()]

def init_db(app=None):
    if app:
        with app.app_context():
            DatabaseInitializer.ensure_db()
    else:
        DatabaseInitializer.ensure_db()
        