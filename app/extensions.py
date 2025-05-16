from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from meilisearch import Client as MeiliClient
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Database
db = SQLAlchemy()
migrate = Migrate()

# Authentication
jwt = JWTManager()

# WebSocket
socketio = SocketIO()

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# CORS
cors = CORS()

# Search
meili = MeiliClient()


def init_extensions(app):
    """Initialize all Flask extensions"""
    # Database
    db.init_app(app)
    migrate.init_app(app, db)

    # Authentication
    jwt.init_app(app)

    # WebSocket
    socketio.init_app(app, cors_allowed_origins="*")

    # Rate Limiting
    limiter.init_app(app)

    # CORS
    cors.init_app(app)

    # Search
    meili.init_app(app)

    # Sentry
    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
        )
