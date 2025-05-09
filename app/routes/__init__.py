from .auth import auth_bp
from .wardrobe import wardrobe_bp
from .fit import fit_bp
from .feed import feed_bp
from .bid import bid_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(wardrobe_bp, url_prefix="/api/wardrobe")
    app.register_blueprint(fit_bp, url_prefix="/api/fits")
    app.register_blueprint(feed_bp, url_prefix="/api/feed")
    app.register_blueprint(bid_bp, url_prefix="/api/bid")
