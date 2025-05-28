from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.wardrobe import Wardrobe
from app.models.clothing_item import Item

wardrobe_bp = Blueprint("wardrobe", __name__)


@wardrobe_bp.route("/wardrobes", methods=["POST"])
@jwt_required()
def create_wardrobe():
    data = request.get_json()
    name = data.get("name")
    user_id = get_jwt_identity()

    if not name:
        return jsonify({"error": "Name is required"}), 400

    wardrobe = Wardrobe(name=name, user_id=user_id)
    db.session.add(wardrobe)
    db.session.commit()

    return (
        jsonify(
            {"message": "Wardrobe created successfully", "wardrobe_id": wardrobe.id}
        ),
        201,
    )


@wardrobe_bp.route("/wardrobes/<string:wardrobe_id>", methods=["GET"])
@jwt_required()
def get_wardrobe(wardrobe_id):
    try:
        wardrobe = Wardrobe.query.get_or_404(wardrobe_id)
        return jsonify(wardrobe.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred", "message": str(e)}), 500
    except Exception as e:
        return (
            jsonify({"error": "An unexpected error occurred", "message": str(e)}),
            500,
        )


@wardrobe_bp.route("/wardrobes/<string:wardrobe_id>/items", methods=["POST"])
@jwt_required()
def add_clothing_item(wardrobe_id):
    user_id = get_jwt_identity()
    wardrobe = Wardrobe.query.get_or_404(wardrobe_id)

    # Check if user owns the wardrobe
    # if wardrobe.user_id != user_id:
    #     return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    # Validate required fields
    if not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    # Validate and convert price
    price = data.get("price")
    if price is not None:
        try:
            # Remove any currency symbols and convert to float
            price = float(str(price).replace("$", "").replace(",", "").strip())
        except (ValueError, TypeError):
            return jsonify({"error": "Price must be a valid number"}), 400

    # Create new item
    item = Item(
        user_id=user_id,
        name=data.get("name"),
        description=data.get("description"),
        category=data.get("category"),
        brand=data.get("brand"),
        color=data.get("color"),
        size=data.get("size"),
        condition=data.get("condition"),
        price=price,  # Now using the converted price
        is_public=data.get("is_public", True),
        tags=data.get("tags", []),
    )

    try:
        # Add item to wardrobe
        wardrobe.items.append(item)
        db.session.add(item)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Item added to wardrobe successfully",
                    "item": item.to_dict(),
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred", "message": str(e)}), 500
    except Exception as e:
        return (
            jsonify({"error": "An unexpected error occurred", "message": str(e)}),
            500,
        )
