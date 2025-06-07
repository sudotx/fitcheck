import sentry_sdk
from celery import Celery
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from sentry_sdk.integrations.flask import FlaskIntegration

from app.config import config

# Database
db = SQLAlchemy()
migrate = Migrate()
mongo_client = None
privacy_vault = None

# Authentication
jwt = JWTManager()

mail = Mail()

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# CORS
cors = CORS()

# Initialize Celery
celery = Celery(
    "fitcheck",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.services.ai_service"],
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


def init_extensions(app):
    """Initialize all Flask extensions"""
    global mongo_client, privacy_vault

    # MongoDB Configuration
    mongo_client = MongoClient(
        app.config["MONGODB_URI"],
        server_api=ServerApi("1"),
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=20000,
    )

    # Initialize privacy vault
    privacy_vault = mongo_client[app.config.get("MONGODB_DB", "fitcheck")][
        "privacy_vault"
    ]

    # Other extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app)

    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
        )

    mail.init_app(app)


def init_jwt_callbacks():
    """Initialize JWT callbacks after all models are loaded"""
    from app.models.token_blocklist import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).scalar()
        return token is not None
