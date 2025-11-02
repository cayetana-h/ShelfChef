import sqlite3
from typing import List, Optional, Dict, Any

from .utils import normalize_ingredient


DB_PATH = "recipes.db"

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_db():
    """ensuring the database and tables exist, with necessary schema"""
    conn = _get_connection()
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

    conn.commit()

    cols = [r["name"] for r in c.execute("PRAGMA table_info(my_recipes)").fetchall()]
    if "source" not in cols:
        c.execute("ALTER TABLE my_recipes ADD COLUMN source TEXT DEFAULT 'user'")
    if "api_id" not in cols:
        c.execute("ALTER TABLE my_recipes ADD COLUMN api_id INTEGER")

    conn.commit()
    conn.close()

_ensure_db()

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

def get_user_recipes() -> List[Dict[str, Any]]:
    """retrieving all stored recipes (both user-created and saved-from-API)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, ingredients, instructions, source, api_id FROM my_recipes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [_row_to_recipe(r) for r in rows]

def get_user_recipe(recipe_id: int) -> Optional[Dict[str, Any]]:
    """retrieves a single recipe by ID."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, ingredients, instructions, source, api_id FROM my_recipes WHERE id = ?", (recipe_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_recipe(row)

def save_user_recipe(name: str, ingredients: List[str], instructions: str, source: str = "user", api_id: Optional[int] = None) -> int:
    """
    saves a new recipe to the db + returns new recipe ID
    """
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO my_recipes (name, ingredients, instructions, source, api_id) VALUES (?, ?, ?, ?, ?)",
        (name, ",".join([i.strip() for i in ingredients if i is not None]), instructions, source, api_id)
    )
    conn.commit()
    rowid = c.lastrowid
    conn.close()
    return rowid

def update_user_recipe(recipe_id: int, name: str, ingredients: List[str], instructions: str) -> bool:
    """
    updates an existing user-created recipe
    """
    existing = get_user_recipe(recipe_id)
    if not existing:
        return False
    if existing.get("source") != "user":
        return False

    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE my_recipes SET name = ?, ingredients = ?, instructions = ? WHERE id = ?",
        (name, ",".join([i.strip() for i in ingredients if i is not None]), instructions, recipe_id)
    )
    conn.commit()
    conn.close()
    return True

def delete_user_recipe(recipe_id: int) -> bool:
    """deletes a user-created recipe by ID"""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM my_recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    changed = c.rowcount > 0
    conn.close()
    return changed

def get_common_ingredients_from_db():
    """fetiching common ingredients stored in the db"""
    conn = sqlite3.connect("recipes.db")
    c = conn.cursor()
    c.execute("SELECT name FROM ingredients")  
    rows = c.fetchall()
    conn.close()
    return [normalize_ingredient(row[0]) for row in rows]

# ------------------------
# Cache helpers
# ------------------------
def get_cached_response(query: str) -> Optional[str]:
    """returns cached JSON string for a query if it exists"""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT response FROM cached_responses WHERE query = ?", (query,))
    row = c.fetchone()
    conn.close()
    return row["response"] if row else None

def save_cached_response(query: str, response: str) -> None:
    """saves or updates cache for a query"""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO cached_responses (query, response) VALUES (?, ?)
        ON CONFLICT(query) DO UPDATE SET response=excluded.response
    """, (query, response))
    conn.commit()
    conn.close()