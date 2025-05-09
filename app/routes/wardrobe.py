from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import ClothingItem, Wardrobe

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


@wardrobe_bp.route("/wardrobes/<int:wardrobe_id>", methods=["GET"])
@jwt_required()
def get_wardrobe(wardrobe_id):
    wardrobe = Wardrobe.query.get_or_404(wardrobe_id)
    return (
        jsonify(
            {
                "id": wardrobe.id,
                "name": wardrobe.name,
                "user_id": wardrobe.user_id,
                "items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "size": item.size,
                        "color": item.color,
                    }
                    for item in wardrobe.clothing_items
                ],
            }
        ),
        200,
    )


@wardrobe_bp.route("/wardrobes/<int:wardrobe_id>/items", methods=["POST"])
@jwt_required()
def add_clothing_item(wardrobe_id):
    wardrobe = Wardrobe.query.get_or_404(wardrobe_id)
    data = request.get_json()

    name = data.get("name")
    description = data.get("description")
    size = data.get("size")
    color = data.get("color")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    item = ClothingItem(
        name=name,
        description=description,
        size=size,
        color=color,
        wardrobe_id=wardrobe_id,
    )
    db.session.add(item)
    db.session.commit()

    return (
        jsonify({"message": "Clothing item added successfully", "item_id": item.id}),
        201,
    )
