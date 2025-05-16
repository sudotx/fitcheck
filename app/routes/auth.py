import os
from datetime import timedelta

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User

INSTAGRAM_AUTH_URL = "https://api.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_USER_URL = "https://graph.instagram.com/me"

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()

    # Validate required fields
    required_fields = ["email", "password", "username"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409

    # Create new user
    user = User(
        email=data["email"],
        username=data["username"],
        password_hash=generate_password_hash(data["password"]),
    )

    db.session.add(user)
    db.session.commit()

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

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(data["password"], user.password_hash):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    # In a real implementation, you might want to blacklist the token
    # This is a simple implementation that just returns success
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

    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_celebrity": user.is_celebrity,
        }
    )


@auth_bp.route("/instagram/login")
def instagram_login():
    redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI")
    client_id = os.getenv("INSTAGRAM_APP_ID")
    auth_url = (
        f"{INSTAGRAM_AUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=user_profile"
        f"&response_type=code"
    )
    return jsonify({"auth_url": auth_url})


@auth_bp.route("/instagram/callback")
def instagram_callback():
    code = request.args.get("code")
    redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI")

    # Exchange code for access token
    data = {
        "client_id": os.getenv("INSTAGRAM_APP_ID"),
        "client_secret": os.getenv("INSTAGRAM_APP_SECRET"),
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code,
    }

    token_res = requests.post(INSTAGRAM_TOKEN_URL, data=data)
    token_json = token_res.json()
    access_token = token_json.get("access_token")
    user_id = token_json.get("user_id")

    # Get Instagram user info
    user_info = requests.get(
        f"{INSTAGRAM_USER_URL}?fields=id,username&access_token={access_token}"
    ).json()

    username = user_info["username"]

    # Register or log in user
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username, email=f"{username}@instagram.com", password="social"
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user.id,
        }
    )
