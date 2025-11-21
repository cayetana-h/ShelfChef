from flask import Flask
import os
from .storage import init_db
from .utils import init_cache 

def create_app():
    app = Flask(__name__)  

    app.config.from_object("app.config.Config")

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///recipes.db"  
    )

    init_cache(app)
    init_db(app)

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
