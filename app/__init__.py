import logging
from celery import Celery

from flask import Flask

from .config import config
from .extensions import init_extensions
from .routes import register_routes

celery = Celery(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    init_extensions(app)

    # Register routes
    register_routes(app)

    # Configure Celery
    celery.conf.update(app.config)

    # Configure logging
    logging.basicConfig(
        filename="fitcheck.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Register error handlers
    from .utils.error_handlers import register_error_handlers

    register_error_handlers(app)

    return app
