from flask import Flask

from .auth import auth_bp
from .bid import bid_bp
from .feed import feed_bp
from .health import health_bp
from .item import item_bp
from .user import user_bp

from .fit import fit_bp

# from .search import search_bp
# from .ai import ai_bp

# from .notification import notification_bp
# from .moderation import moderation_bp


def register_routes(app: Flask):
    """Register all route blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(bid_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(item_bp)
    # app.register_blueprint(fit_bp)
    # app.register_blueprint(search_bp)
    # app.register_blueprint(ai_bp)
    # app.register_blueprint(notification_bp)
    # app.register_blueprint(moderation_bp)
