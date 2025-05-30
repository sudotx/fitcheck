from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User
from app.models.user_privacy import UserPrivacy
from app.models.token_blocklist import TokenBlocklist
from app.utils.mail import send_welcome_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()

    # Validate required fields
    required_fields = ["email", "password", "username"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    # existing_privacy = UserPrivacy.get_by_email(data["email"])
    # if existing_privacy:
    #     return jsonify({"error": "Email already registered"}), 409

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409

    # Create new user
    user = User(username=data["username"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    # Create privacy data
    user.update_privacy_data(
        email=data["email"],
        phone=data.get("phone"),
        address=data.get("address"),
        payment_info=data.get("payment_info"),
    )

    # Send welcome email
    try:
        send_welcome_email(user)
    except Exception as e:
        # Log the error but don't fail the signup
        print(f"Failed to send welcome email: {str(e)}")

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return (
        jsonify(
            {
                "message": "User registered successfully",
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        ),
        201,
    )


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    # Find user by email in privacy vault
    privacy_data = UserPrivacy.get_by_email(data["email"])
    if not privacy_data:
        return jsonify({"error": "Invalid email or password"}), 401

    user = User.query.get(privacy_data["user_id"])
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    exp = datetime.fromtimestamp(get_jwt()["exp"])

    # Check if token is already in blocklist
    existing_token = TokenBlocklist.query.filter_by(jti=jti).first()
    if existing_token:
        return jsonify({"message": "Token already invalidated"}), 200

    # Add token to blocklist
    blocklist_entry = TokenBlocklist(jti=jti, expires_at=exp)
    db.session.add(blocklist_entry)
    db.session.commit()

    return jsonify({"message": "Successfully logged out"}), 200


@auth_bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    privacy_data = user.get_privacy_data()

    return jsonify(
        {
            "id": str(user.id),
            "username": user.username,
            "email": privacy_data["email"] if privacy_data else None,
            "is_celebrity": user.is_celebrity,
        }
    )
