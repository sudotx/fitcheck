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
    logging.basicConfig(
        filename="fitcheck.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Register error handlers
    from .utils.error_handlers import register_error_handlers

    register_error_handlers(app)

    # Initialize JWT
    from flask_jwt_extended import JWTManager

    # jwt = JWTManager(app)
    app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = config.JWT_ACCESS_TOKEN_EXPIRES
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = config.JWT_REFRESH_TOKEN_EXPIRES
    app.config["JWT_BLOCKLIST_ENABLED"] = True
    app.config["JWT_BLOCKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

    # MailerSend SMTP configuration
    app.config["MAIL_SERVER"] = "smtp.mailersend.net"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = config.MAIL_USERNAME  # Your MailerSend SMTP username
    app.config["MAIL_PASSWORD"] = config.MAIL_PASSWORD  # Your MailerSend SMTP password
    app.config["MAIL_DEFAULT_SENDER"] = config.MAIL_DEFAULT_SENDER
    app.config["MAIL_MAX_EMAILS"] = 100
    app.config["MAIL_ASCII_ATTACHMENTS"] = False
    app.config["MAIL_USE_SSL"] = False

    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

    # Initialize JWT callbacks after all models are loaded
    init_jwt_callbacks()

    return app
