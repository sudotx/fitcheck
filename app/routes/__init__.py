from flask import Flask

from .auth import auth_bp
from .user import user_bp
from .item import item_bp
from .outfit import outfit_bp
from .search import search_bp
from .ai import ai_bp
from .feed import feed_bp
from .notification import notification_bp
from .moderation import moderation_bp
from .health import health_bp


def register_routes(app: Flask):
    """Register all route blueprints with the Flask application."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(outfit_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(moderation_bp)
    app.register_blueprint(health_bp)
