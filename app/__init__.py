from flask import Flask
import os 

def create_app():
    app = Flask(__name__)  

    app.config.from_object("app.config.Config")

    if not hasattr(app, "recipe_cache"):
        app.recipe_cache = {}

    if not hasattr(app, "ingredient_cache"):
        app.ingredient_cache = {}

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    with app.app_context():
        from .storage import _ensure_db
        _ensure_db()

    return app
