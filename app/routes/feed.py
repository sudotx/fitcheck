from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User, Fit

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/feed", methods=["GET"])
@jwt_required()
def get_feed():
    # Simple feed: get all fits from other users
    current_user_id = get_jwt_identity()
    fits = Fit.query.join(User).filter(User.id != current_user_id).all()

    return (
        jsonify(
            [
                {
                    "id": fit.id,
                    "name": fit.name,
                    "user_id": fit.user_id,
                    "username": fit.user.username,
                }
                for fit in fits
            ]
        ),
        200,
    )
