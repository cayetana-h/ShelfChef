from flask import Flask
from .storage import init_db
from .utils import init_cache 

def create_app():
    app = Flask(__name__)  

    app.config.from_object("app.config.Config")

    init_cache(app)
    init_db(app)

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)


    return app
