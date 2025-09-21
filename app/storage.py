import sqlite3

DB_PATH = "recipes.db"

def get_user_recipes():
    """Retrieve all user-created recipes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, ingredients, instructions FROM my_recipes")
    rows = c.fetchall()
    conn.close()

    recipes = []
    for row in rows:
        recipes.append({
            "id": row[0],
            "name": row[1],
            "ingredients": row[2].split(","),
            "instructions": row[3]
        })
    return recipes

def save_user_recipe(name, ingredients, instructions):
    """Save a new user-created recipe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO my_recipes (name, ingredients, instructions) VALUES (?, ?, ?)",
        (name, ",".join(ingredients), instructions)
    )
    conn.commit()
    conn.close()
