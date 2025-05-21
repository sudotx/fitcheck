from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def healthcheck():
    try:
        # Check database connection
        db.session.execute(text("SELECT 1")).fetchone()
        return (
            jsonify(
                {
                    "status": "healthy",
                    "database": "connected",
                    "message": "All systems operational",
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "error": str(e),
                    "message": "Database connection failed",
                }
            ),
            500,
        )
