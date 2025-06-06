from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.ai_service import (
    ai_service,
)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai/embed/item/<string:item_id>", methods=["POST"])
@jwt_required()
def embed_item(item_id):
    """
    Generate embedding for an item asynchronously

    Args:
        item_id (str): The ID of the item to generate embedding for

    Returns:
        JSON response with task ID
    """
    user_id = get_jwt_identity()

    # Trigger async task for embedding generation
    task = ai_service.generate_item_embedding.delay(item_id)

    return (
        jsonify(
            {
                "message": "Embedding generation started",
                "task_id": task.id,
            }
        ),
        202,
    )


@ai_bp.route("/ai/tags/item/<string:item_id>", methods=["POST"])
@jwt_required()
def tag_item(item_id):
    """
    Generate tags for an item asynchronously

    Args:
        item_id (str): The ID of the item to generate tags for

    Returns:
        JSON response with task ID
    """
    user_id = get_jwt_identity()

    # Trigger async task for tag generation
    task = ai_service.generate_item_tags.delay(item_id)

    return jsonify({"message": "Tag generation started", "task_id": task.id}), 202


@ai_bp.route("/ai/recommendations", methods=["GET"])
@jwt_required()
def get_personalized_recommendations():
    """
    Get personalized item recommendations for the authenticated user.

    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of items per page (default: 20)

    Returns:
    - JSON response with paginated recommendations
    """
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    recommendations = ai_service.get_recommendations(
        user_id=user_id, page=page, per_page=per_page
    )

    return jsonify(recommendations), 200
