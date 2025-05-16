from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Outfit, OutfitItem, Like, Comment

outfit_bp = Blueprint("outfit", __name__)


@outfit_bp.route("/outfits", methods=["GET"])
def list_outfits():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    outfits = (
        Outfit.query.filter_by(is_public=True)
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


@outfit_bp.route("/outfits", methods=["POST"])
@jwt_required()
def create_outfit():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get("items"):
        return jsonify({"error": "At least one item is required"}), 400

    outfit = Outfit(
        user_id=user_id,
        name=data.get("name"),
        description=data.get("description"),
        is_public=data.get("is_public", True),
    )

    db.session.add(outfit)
    db.session.flush()  # Get outfit ID before commit

    # Add items to outfit
    for item_id in data["items"]:
        outfit_item = OutfitItem(outfit_id=outfit.id, item_id=item_id)
        db.session.add(outfit_item)

    db.session.commit()
    return jsonify(outfit.to_dict()), 201


@outfit_bp.route("/outfits/<int:outfit_id>", methods=["GET"])
def get_outfit(outfit_id):
    outfit = Outfit.query.get_or_404(outfit_id)
    if not outfit.is_public:
        return jsonify({"error": "Outfit not found"}), 404
    return jsonify(outfit.to_dict()), 200


@outfit_bp.route("/outfits/<int:outfit_id>", methods=["PATCH"])
@jwt_required()
def update_outfit(outfit_id):
    user_id = get_jwt_identity()
    outfit = Outfit.query.get_or_404(outfit_id)

    if outfit.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    allowed_fields = ["name", "description", "is_public"]

    for field in allowed_fields:
        if field in data:
            setattr(outfit, field, data[field])

    if "items" in data:
        # Remove existing items
        OutfitItem.query.filter_by(outfit_id=outfit.id).delete()

        # Add new items
        for item_id in data["items"]:
            outfit_item = OutfitItem(outfit_id=outfit.id, item_id=item_id)
            db.session.add(outfit_item)

    db.session.commit()
    return jsonify(outfit.to_dict()), 200


@outfit_bp.route("/outfits/<int:outfit_id>", methods=["DELETE"])
@jwt_required()
def delete_outfit(outfit_id):
    user_id = get_jwt_identity()
    outfit = Outfit.query.get_or_404(outfit_id)

    if outfit.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(outfit)
    db.session.commit()
    return jsonify({"message": "Outfit deleted successfully"}), 200


@outfit_bp.route("/outfits/<int:outfit_id>/like", methods=["POST"])
@jwt_required()
def like_outfit(outfit_id):
    user_id = get_jwt_identity()

    if Like.query.filter_by(user_id=user_id, outfit_id=outfit_id).first():
        return jsonify({"error": "Already liked this outfit"}), 400

    like = Like(user_id=user_id, outfit_id=outfit_id)
    db.session.add(like)
    db.session.commit()

    return jsonify({"message": "Outfit liked successfully"}), 200


@outfit_bp.route("/outfits/<int:outfit_id>/unlike", methods=["POST"])
@jwt_required()
def unlike_outfit(outfit_id):
    user_id = get_jwt_identity()
    like = Like.query.filter_by(user_id=user_id, outfit_id=outfit_id).first_or_404()

    db.session.delete(like)
    db.session.commit()

    return jsonify({"message": "Outfit unliked successfully"}), 200


@outfit_bp.route("/outfits/<int:outfit_id>/comment", methods=["POST"])
@jwt_required()
def add_comment(outfit_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get("content"):
        return jsonify({"error": "Comment content is required"}), 400

    comment = Comment(user_id=user_id, outfit_id=outfit_id, content=data["content"])

    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict()), 201


@outfit_bp.route("/outfits/<int:outfit_id>/comments", methods=["GET"])
def get_comments(outfit_id):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    comments = (
        Comment.query.filter_by(outfit_id=outfit_id)
        .order_by(Comment.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "comments": [comment.to_dict() for comment in comments.items],
                "total": comments.total,
                "pages": comments.pages,
                "current_page": comments.page,
            }
        ),
        200,
    )
