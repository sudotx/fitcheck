from datetime import datetime
from app.models.clothing_item import AuctionStatus, Item
from app.models.user import User
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db

from app.models.bid import Bid

from uuid import uuid4

bid_bp = Blueprint("bid", __name__)


@bid_bp.route("/bids", methods=["POST"])
@jwt_required()
def create_bid():
    data = request.get_json()
    amount = data.get("amount")
    item_id = data.get("item_id")
    user_id = get_jwt_identity()

    if not amount or not user_id:
        return jsonify({"error": "Amount and user_id are required"}), 400

    # check if the item is still active
    item = Item.query.get_or_404(item_id)
    if item.auction_status != AuctionStatus.ACTIVE:
        return jsonify({"error": "Item is not active"}), 400

    # check if the user has enough balance
    user = User.query.get_or_404(user_id)
    if user.balance < amount + user.temp_balance_hold:
        return jsonify({"error": "User does not have enough balance to bid"}), 400

    if user.lightning_address and user.balance < amount + user.temp_balance_hold:
        return (
            jsonify({"error": "User does not have enough balance in their wallet"}),
            400,
        )
    # Put a hold on the user's account for the bid amount
    user.temp_balance_hold += amount
    db.session.commit()

    # check if the bid is higher than the current bid
    if item.auction_current_bid and amount <= item.auction_current_bid:
        # check if the user has enough balance to outbid the current bid
        if user.balance < amount - item.auction_current_bid:
            return (
                jsonify(
                    {
                        "error": "User does not have enough balance to outbid the current bid"
                    }
                ),
                400,
            )

        # update the current bid
        item.auction_current_bid = amount
        item.auction_current_bidder_id = user_id
        item.auction_current_bid_at = datetime.utcnow()
        return jsonify({"error": "Bid is not higher than the current bid"}), 400

    bid = Bid(amount=amount, user_id=user_id, item_id=item_id)
    db.session.add(bid)
    db.session.commit()

    return jsonify({"message": "Bid created successfully", "bid_id": bid.id}), 201


@bid_bp.route("/bids/<string:bid_id>", methods=["GET"])
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
