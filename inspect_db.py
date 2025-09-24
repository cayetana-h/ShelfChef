import sqlite3

conn = sqlite3.connect("recipes.db")
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", c.fetchall())

c.execute("SELECT * FROM ingredients LIMIT 10;")
print("Ingredients:", c.fetchall())

conn.close()
