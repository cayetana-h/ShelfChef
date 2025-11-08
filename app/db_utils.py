import sqlite3
from contextlib import contextmanager
from flask import current_app

def _get_connection():
    conn = sqlite3.connect(current_app.config.get("DATABASE_PATH", "recipes.db"))
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def db_connection():
    conn = _get_connection()
    try:
        yield conn
    finally:
        conn.close()