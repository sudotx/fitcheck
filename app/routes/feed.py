from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models.clothing_item import Item
from app.services.recommendation_service import RecommendationEngine

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/feed/home", methods=["GET"])
@jwt_required()
def get_home_feed():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get personalized recommendations
    recommendation = RecommendationEngine.recommend_outfit(user_id)

    if "error" in recommendation:
        return jsonify({"error": recommendation["error"]}), 400

    return (
        jsonify(
            {
                "outfit": recommendation["outfit"],
                "confidence": recommendation["confidence"],
                "color_palette": recommendation["color_palette"],
                "generated_at": recommendation["generated_at"],
            }
        ),
        200,
    )


@feed_bp.route("/feed/trending", methods=["GET"])
def get_trending_feed():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get trending items based on likes and recent activity
    items = (
        Item.query.filter_by(is_public=True)
        .order_by(Item.likes_count.desc(), Item.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "items": [item.to_dict() for item in items.items],
                "total": items.total,
                "pages": items.pages,
                "current_page": items.page,
            }
        ),
        200,
    )


@feed_bp.route("/feed/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    occasion = request.args.get("occasion")
    weather = request.args.get("weather")

    # Get contextual recommendations
    recommendation = RecommendationEngine.recommend_outfit(
        user_id=user_id, occasion=occasion, weather=weather
    )

    if "error" in recommendation:
        return jsonify({"error": recommendation["error"]}), 400

    return (
        jsonify(
            {
                "outfit": recommendation["outfit"],
                "confidence": recommendation["confidence"],
                "color_palette": recommendation["color_palette"],
                "generated_at": recommendation["generated_at"],
            }
        ),
        200,
    )
