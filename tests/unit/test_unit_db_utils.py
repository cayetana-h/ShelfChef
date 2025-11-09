import sqlite3
import pytest
from flask import Flask
from app import db_utils

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = ":memory:"
    return app

def test_get_connection_returns_valid_connection(app):
    with app.app_context():
        conn = db_utils._get_connection()
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row
        conn.close()

def test_get_connection_uses_configured_database_path(app, monkeypatch):
    mock_path = "test_recipes.db"
    app.config["DATABASE_PATH"] = mock_path
    with app.app_context():
        conn = db_utils._get_connection()
        assert conn is not None
        conn.close()

def test_db_connection_context_manager_closes_connection(app):
    with app.app_context():
        with db_utils.db_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
