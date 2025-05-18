from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Fit, Follow, Item

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/feed/home", methods=["GET"])
@jwt_required()
def get_home_feed():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get fits from followed users and trending items
    followed_users = (
        Follow.query.filter_by(follower_id=user_id)
        .with_entities(Follow.following_id)
        .all()
    )
    followed_user_ids = [f[0] for f in followed_users]

    fits = (
        Fit.query.filter(Fit.user_id.in_(followed_user_ids), Fit.is_public == True)
        .order_by(Fit.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "fits": [fit.to_dict() for fit in fits.items],
                "total": fits.total,
                "pages": fits.pages,
                "current_page": fits.page,
            }
        ),
        200,
    )


@feed_bp.route("/feed/trending", methods=["GET"])
def get_trending_feed():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Get trending fits based on likes and recent activity
    fits = (
        Fit.query.filter_by(is_public=True)
        .order_by(Fit.likes_count.desc(), Fit.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "fits": [outfit.to_dict() for outfit in fits.items],
                "total": fits.total,
                "pages": fits.pages,
                "current_page": fits.page,
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
