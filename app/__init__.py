from flask import Flask
import os
from .storage import init_db
from .utils import init_cache 
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import CollectorRegistry

def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///recipes.db"
    )

    init_cache(app)
    init_db(app)
    from .routes import bp as routes_bp, health_bp
    app.register_blueprint(routes_bp)
    app.register_blueprint(health_bp)

    if testing:
        from prometheus_client import CollectorRegistry
        from prometheus_flask_exporter import PrometheusMetrics
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(app, registry=registry)
    else:
        from prometheus_flask_exporter import PrometheusMetrics
        metrics = PrometheusMetrics(app)

    metrics.info('app_info', 'Application info', version='1.0')

    return app