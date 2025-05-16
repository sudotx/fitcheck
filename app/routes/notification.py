from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Notification, User

notification_bp = Blueprint("notification", __name__)


@notification_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    notifications = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "notifications": [
                    notification.to_dict() for notification in notifications.items
                ],
                "total": notifications.total,
                "pages": notifications.pages,
                "current_page": notifications.page,
            }
        ),
        200,
    )


@notification_bp.route("/notifications/read", methods=["POST"])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()

    Notification.query.filter_by(user_id=user_id, is_read=False).update(
        {"is_read": True}
    )

    db.session.commit()
    return jsonify({"message": "All notifications marked as read"}), 200


@notification_bp.route("/notifications/token", methods=["POST"])
@jwt_required()
def register_push_token():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get("token"):
        return jsonify({"error": "Push token is required"}), 400

    # Update user's push token
    user = User.query.get(user_id)
    user.push_token = data["token"]
    db.session.commit()

    return jsonify({"message": "Push token registered successfully"}), 200
