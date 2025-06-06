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
from sentry_sdk.integrations.flask import FlaskIntegration

from app.config import config

# Database
db = SQLAlchemy()
migrate = Migrate()

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

# MongoDB client for privacy vault
mongo_client = MongoClient(
    config.MONGODB_URI,
    username=config.MONGODB_USERNAME,
    password=config.MONGODB_PASSWORD,
)
privacy_vault = mongo_client[config.MONGODB_DB]


def init_mongodb():
    """Initialize MongoDB collections"""
    # Create index for user_id uniqueness
    privacy_vault.user_privacy.create_index("user_id", unique=True)


def init_extensions(app):
    """Initialize all Flask extensions"""
    # Database
    db.init_app(app)
    migrate.init_app(app, db)

    # MongoDB
    init_mongodb()

    # Authentication
    jwt.init_app(app)

    # Rate Limiting
    limiter.init_app(app)

    # CORS
    cors.init_app(app)

    # Sentry
    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
        )

    # Mail
    mail.init_app(app)


def init_jwt_callbacks():
    """Initialize JWT callbacks after all models are loaded"""
    from app.models.token_blocklist import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).scalar()
        return token is not None
