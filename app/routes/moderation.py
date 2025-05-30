from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Report, Block

moderation_bp = Blueprint("moderation", __name__)


@moderation_bp.route("/moderation/report", methods=["POST"])
@jwt_required()
def report_content():
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ["content_type", "content_id", "reason"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    report = Report(
        reporter_id=user_id,
        content_type=data["content_type"],
        content_id=data["content_id"],
        reason=data["reason"],
        details=data.get("details"),
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({"message": "Report submitted successfully"}), 201


@moderation_bp.route("/moderation/block/<string:user_id>", methods=["POST"])
@jwt_required()
def block_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id == user_id:
        return jsonify({"error": "Cannot block yourself"}), 400

    if Block.query.filter_by(blocker_id=current_user_id, blocked_id=user_id).first():
        return jsonify({"error": "User already blocked"}), 400

    block = Block(blocker_id=current_user_id, blocked_id=user_id)
    db.session.add(block)
    db.session.commit()

    return jsonify({"message": "User blocked successfully"}), 200


@moderation_bp.route("/moderation/unblock/<string:user_id>", methods=["POST"])
@jwt_required()
def unblock_user(user_id):
    current_user_id = get_jwt_identity()

    block = Block.query.filter_by(
        blocker_id=current_user_id, blocked_id=user_id
    ).first_or_404()

    db.session.delete(block)
    db.session.commit()

    return jsonify({"message": "User unblocked successfully"}), 200
