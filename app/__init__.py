from flask import Flask
import os 

def create_app():
    app = Flask(__name__)  

    app.config.from_object("app.config.Config")

    if not hasattr(app, "recipe_cache"):
        app.recipe_cache = {}

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
