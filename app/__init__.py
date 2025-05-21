import logging
from celery import Celery
from celery.schedules import crontab

from flask import Flask

from .config import config
from .extensions import init_extensions, init_jwt_callbacks
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

    # Configure Celery Beat schedule
    celery.conf.beat_schedule = {
        "cleanup-expired-tokens": {
            "task": "app.tasks.cleanup_expired_tokens",
            "schedule": crontab(hour="*/1"),  # Run every hour
        },
    }

    # Configure logging
    # logging.basicConfig(
    #     filename="fitcheck.log",
    #     level=logging.INFO,
    #     format="%(asctime)s - %(levelname)s - %(message)s",
    # )

    # Register error handlers
    from .utils.error_handlers import register_error_handlers

    register_error_handlers(app)

    # Initialize JWT
    from flask_jwt_extended import JWTManager

    jwt = JWTManager(app)
    app.config["JWT_BLOCKLIST_ENABLED"] = True
    app.config["JWT_BLOCKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

    # Initialize JWT callbacks after all models are loaded
    init_jwt_callbacks()

    return app
