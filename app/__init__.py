from flask import Flask

def create_app():
    app = Flask(__name__)  

    app.secret_key = "super-secret-key" 

    from .routes import init_routes
    init_routes(app)

    return app
