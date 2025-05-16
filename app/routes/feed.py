from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User, Fit, Outfit, Item, Follow

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/feed/home", methods=["GET"])
@jwt_required()
def get_home_feed():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get outfits from followed users and trending items
    followed_users = (
        Follow.query.filter_by(follower_id=user_id)
        .with_entities(Follow.following_id)
        .all()
    )
    followed_user_ids = [f[0] for f in followed_users]

    outfits = (
        Outfit.query.filter(
            Outfit.user_id.in_(followed_user_ids), Outfit.is_public == True
        )
        .order_by(Outfit.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "outfits": [outfit.to_dict() for outfit in outfits.items],
                "total": outfits.total,
                "pages": outfits.pages,
                "current_page": outfits.page,
            }
        ),
        200,
    )


@feed_bp.route("/feed/trending", methods=["GET"])
def get_trending_feed():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get trending outfits based on likes and recent activity
    outfits = (
        Outfit.query.filter_by(is_public=True)
        .order_by(Outfit.likes_count.desc(), Outfit.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "outfits": [outfit.to_dict() for outfit in outfits.items],
                "total": outfits.total,
                "pages": outfits.pages,
                "current_page": outfits.page,
            }
        ),
        200,
    )


@feed_bp.route("/feed/following", methods=["GET"])
@jwt_required()
def get_following_feed():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get items from followed users
    followed_users = (
        Follow.query.filter_by(follower_id=user_id)
        .with_entities(Follow.following_id)
        .all()
    )
    followed_user_ids = [f[0] for f in followed_users]

    items = (
        Item.query.filter(Item.user_id.in_(followed_user_ids), Item.is_public == True)
        .order_by(Item.created_at.desc())
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
