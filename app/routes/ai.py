from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.ai_service import (
    generate_item_embedding,
    generate_item_tags,
    get_recommendations,
)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai/embed/item/<int:item_id>", methods=["POST"])
@jwt_required()
def embed_item(item_id):
    user_id = get_jwt_identity()

    # Trigger async task for embedding generation
    task = generate_item_embedding.delay(item_id)

    return jsonify({"message": "Embedding generation started", "task_id": task.id}), 202


@ai_bp.route("/ai/tags/item/<int:item_id>", methods=["POST"])
@jwt_required()
def tag_item(item_id):
    user_id = get_jwt_identity()

    # Trigger async task for tag generation
    task = generate_item_tags.delay(item_id)

    return jsonify({"message": "Tag generation started", "task_id": task.id}), 202


@ai_bp.route("/ai/recommendations", methods=["GET"])
@jwt_required()
def get_personalized_recommendations():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    recommendations = get_recommendations(user_id=user_id, page=page, per_page=per_page)

    return (
        jsonify(
            {
                "items": [item.to_dict() for item in recommendations.items],
                "total": recommendations.total,
                "pages": recommendations.pages,
                "current_page": recommendations.page,
            }
        ),
        200,
    )
