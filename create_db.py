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

conn.commit()
conn.close()
print("Database ready for user recipes.")
