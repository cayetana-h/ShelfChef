import sqlite3
from typing import List, Optional, Dict, Any

DB_PATH = "recipes.db"

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_db():
    """
    Ensure the `my_recipes` table exists and has the expected columns.
    This will create the table if it doesn't exist and add missing columns (source, api_id).
    """
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
    """Retrieve all stored recipes (both user-created and saved-from-API)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, ingredients, instructions, source, api_id FROM my_recipes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [_row_to_recipe(r) for r in rows]

def get_user_recipe(recipe_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single recipe by ID."""
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
    Save a new recipe.
    - source: 'user' (default) or 'api'
    - api_id: optional integer ID from upstream API (if source == 'api')
    Returns the inserted row id.
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
    Update a recipe only if it's user-created. Returns True if updated, False otherwise.
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
    """Delete a recipe by ID. Returns True if a row was deleted."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM my_recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    changed = c.rowcount > 0
    conn.close()
    return changed
