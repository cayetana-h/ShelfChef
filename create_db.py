import sqlite3

conn = sqlite3.connect('recipes.db')
c = conn.cursor()

# Table for user-created or saved recipes
c.execute('''
CREATE TABLE IF NOT EXISTS my_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS cached_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT UNIQUE NOT NULL,
    response TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
''')

common_ingredients = [
    "onion", "garlic", "tomato", "chicken", "beef", "egg",
    "milk", "cheese", "butter", "flour", "rice", "potato",
    "carrot", "bell pepper", "spinach", "salt", "pepper", "sugar", "pasta",
    "olive oil", "vinegar", "basil", "oregano", "cumin", "paprika"
]

c.executemany('''
INSERT OR IGNORE INTO ingredients (name) VALUES (?)
''', [(ingredient,) for ingredient in common_ingredients])

conn.commit()
conn.close()
print("Database ready with user recipes, cache, and ingredients.")
