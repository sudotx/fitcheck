from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User


def admin_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if (
                not user or not user.is_celebrity
            ):  # Using is_celebrity as admin indicator
                return jsonify({"error": "Admin access required"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
