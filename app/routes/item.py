from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
import json
from datetime import datetime

from app.extensions import db
from app.models.clothing_item import Item, AuctionStatus

from app.services.ai_service import ai_service
from app.utils.image_handler import image_handler

item_bp = Blueprint("item", __name__)


@item_bp.route("/items", methods=["GET"])
def list_items():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    items = (
        Item.query.filter_by(is_public=True)
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


@item_bp.route("/items", methods=["POST"])
@jwt_required()
def create_item():
    user_id = get_jwt_identity()
    data = request.form

    # Validate required fields
    required_fields = [
        "title",
        "size_type",
        "size_value",
        "size_compatibility",
        "price",
    ]
    if not all(field in data for field in required_fields):
        return (
            jsonify(
                {"error": f"Missing required fields: {', '.join(required_fields)}"}
            ),
            400,
        )

    # Validate image
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files["image"]
    upload_result = image_handler.upload_to_cloudinary(image_file, "items")

    if not upload_result:
        return jsonify({"error": "Failed to upload image"}), 400

    try:
        # Parse size compatibility JSON
        size_compatibility = json.loads(data.get("size_compatibility"))

        # Create item with all required fields
        item = Item(
            user_id=user_id,
            title=data.get("title"),
            description=data.get("description"),
            category=data.get("category"),
            size_type=data.get("size_type"),
            size_value=data.get("size_value"),
            size_compatibility=size_compatibility,
            price=data.get("price"),  # Regular price field
            # Optional fields
            brand=data.get("brand"),
            condition=data.get("condition"),
            tags=json.loads(data.get("tags", "[]")),
            is_public=data.get("is_public", "true").lower() == "true",
            # Image fields
            image_url=upload_result["original_url"],
            thumbnail_url=upload_result["thumbnail_url"],
            cloudinary_public_id=upload_result["public_id"],
        )

        db.session.add(item)
        db.session.commit()

        # Trigger async tasks for AI processing
        ai_service.generate_item_embedding.delay(item.id)
        ai_service.generate_item_tags.delay(item.id)
        ai_service.extract_dominant_colors.delay(item.id)

        return (
            jsonify({"message": "Item created successfully", "item": item.to_dict()}),
            201,
        )

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid size_compatibility or tags JSON format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create item: {str(e)}"}), 500


@item_bp.route("/items/<string:item_id>", methods=["GET"])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    if not item.is_public:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item.to_dict()), 200


@item_bp.route("/items/<string:item_id>", methods=["PATCH"])
@jwt_required()
def update_item(item_id):
    user_id = get_jwt_identity()
    item = Item.query.get_or_404(item_id)

    if item.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    allowed_fields = ["name", "description", "category", "is_public"]

    for field in allowed_fields:
        if field in data:
            setattr(item, field, data[field])

    if "image" in request.files:
        image_file = request.files["image"]
        upload_result = image_handler.upload_to_cloudinary(image_file, "items")
        if not upload_result:
            return jsonify({"error": "Failed to upload image"}), 400
        item.image_url = upload_result["original_url"]
        item.thumbnail_url = upload_result["thumbnail_url"]
        item.cloudinary_public_id = upload_result["public_id"]

    db.session.commit()
    return jsonify(item.to_dict()), 200


@item_bp.route("/items/<string:item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(item_id):
    user_id = get_jwt_identity()
    item = Item.query.get_or_404(item_id)

    if item.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted successfully"}), 200


@item_bp.route("/items/<uuid:item_id>/start-auction", methods=["POST"])
@jwt_required()
def start_auction(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate required auction fields
    required_fields = ["auction_start_price", "auction_ends_at"]
    if not all(field in data for field in required_fields):
        return (
            jsonify(
                {"error": f"Missing required fields: {', '.join(required_fields)}"}
            ),
            400,
        )

    # Get the item and verify ownership
    item = Item.query.get_or_404(item_id)
    if item.user_id != user_id:
        return jsonify({"error": "Unauthorized to modify this item"}), 403

    # Check if item already has an active auction
    if item.auction_status == AuctionStatus.ACTIVE:
        return jsonify({"error": "Item already has an active auction"}), 400

    try:
        # Parse auction end time
        auction_ends_at = datetime.fromisoformat(data.get("auction_ends_at"))

        # Update item with auction details
        item.auction_start_price = data.get("auction_start_price")
        item.auction_ends_at = auction_ends_at
        item.auction_status = AuctionStatus.ACTIVE
        item.auction_current_bid = None  # Reset current bid
        item.auction_current_bidder_id = None  # Reset current bidder

        db.session.commit()

        return (
            jsonify(
                {"message": "Auction started successfully", "item": item.to_dict()}
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to start auction: {str(e)}"}), 500
