from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import User

user_bp = Blueprint("user", __name__)


@user_bp.route("/users/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@user_bp.route("/users/me", methods=["PATCH"])
@jwt_required()
def update_current_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    # Update allowed fields
    allowed_fields = ["username", "bio", "profile_picture", "location"]
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify(user.to_dict()), 200


@user_bp.route("/users/<string:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200
