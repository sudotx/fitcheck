from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def healthcheck():
    try:
        # Check database connection
        db.session.execute("SELECT 1")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@health_bp.route("/metrics", methods=["GET"])
@jwt_required()
def metrics():
    # Only allow admin users to access metrics
    # This should be implemented in a more secure way in production
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
