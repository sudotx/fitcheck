import os

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
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


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    refresh_token = create_refresh_token(identity=user.id)

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=user.id)
    return (
        jsonify(
            {
                "token": token,
                "user_id": user.id,
                "refresh_token": refresh_token,
            }
        ),
        200,
    )


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    return jsonify({"token": new_token}), 200


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
