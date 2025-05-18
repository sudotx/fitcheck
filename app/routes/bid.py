from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Bid

bid_bp = Blueprint("bid", __name__)


@bid_bp.route("/bids", methods=["POST"])
@jwt_required()
def create_bid():
    data = request.get_json()
    amount = data.get("amount")
    user_id = get_jwt_identity()

    if not amount or not user_id:
        return jsonify({"error": "Amount and user_id are required"}), 400

    bid = Bid(amount=amount, user_id=user_id)
    db.session.add(bid)
    db.session.commit()

    return jsonify({"message": "Bid created successfully", "bid_id": bid.id}), 201


@bid_bp.route("/bids/<int:bid_id>", methods=["GET"])
@jwt_required()
def get_bid(bid_id):
    bid = Bid.query.get_or_404(bid_id)
    return jsonify({"id": bid.id, "amount": bid.amount, "user_id": bid.user_id}), 200


@bid_bp.route("/bids", methods=["GET"])
@jwt_required()
def get_user_bids():
    user_id = get_jwt_identity()
    bids = Bid.query.filter_by(user_id=user_id).all()
    return (
        jsonify(
            [
                {"id": bid.id, "amount": bid.amount, "user_id": bid.user_id}
                for bid in bids
            ]
        ),
        200,
    )
