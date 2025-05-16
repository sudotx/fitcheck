from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import User, Follow

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


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@user_bp.route("/users/<int:user_id>/follow", methods=["POST"])
@jwt_required()
def follow_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id == user_id:
        return jsonify({"error": "Cannot follow yourself"}), 400

    if Follow.query.filter_by(
        follower_id=current_user_id, following_id=user_id
    ).first():
        return jsonify({"error": "Already following this user"}), 400

    follow = Follow(follower_id=current_user_id, following_id=user_id)
    db.session.add(follow)
    db.session.commit()

    return jsonify({"message": "Successfully followed user"}), 200


@user_bp.route("/users/<int:user_id>/unfollow", methods=["POST"])
@jwt_required()
def unfollow_user(user_id):
    current_user_id = get_jwt_identity()

    follow = Follow.query.filter_by(
        follower_id=current_user_id, following_id=user_id
    ).first_or_404()

    db.session.delete(follow)
    db.session.commit()

    return jsonify({"message": "Successfully unfollowed user"}), 200


@user_bp.route("/users/<int:user_id>/followers", methods=["GET"])
def get_followers(user_id):
    followers = Follow.query.filter_by(following_id=user_id).all()
    return jsonify([f.follower.to_dict() for f in followers]), 200


@user_bp.route("/users/<int:user_id>/following", methods=["GET"])
def get_following(user_id):
    following = Follow.query.filter_by(follower_id=user_id).all()
    return jsonify([f.following.to_dict() for f in following]), 200
