from flask_socketio import emit, join_room, leave_room
from ..extensions import socketio
from ..models.bid import Bid
from ..models.clothing_item import ClothingItem
from ..services.notification_service import notification_service


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    emit("connected", {"data": "Connected"})


@socketio.on("join_item_room")
def handle_join_item_room(item_id):
    """Join a room for a specific item's bidding"""
    join_room(f"item_{item_id}")
    emit("joined_room", {"room": f"item_{item_id}"})


@socketio.on("leave_item_room")
def handle_leave_item_room(item_id):
    """Leave a room for a specific item's bidding"""
    leave_room(f"item_{item_id}")
    emit("left_room", {"room": f"item_{item_id}"})


@socketio.on("place_bid")
def handle_place_bid(data):
    """Handle new bid placement"""
    item_id = data.get("item_id")
    user_id = data.get("user_id")
    amount = data.get("amount")

    # Create new bid
    bid = Bid(item_id=item_id, user_id=user_id, amount=amount)

    # Broadcast to all clients in the room
    emit(
        "new_bid",
        {"item_id": item_id, "user_id": user_id, "amount": amount},
        room=f"item_{item_id}",
    )

    # Send notification to item owner
    item = ClothingItem.query.get(item_id)
    if item:
        notification_service.send_bid_notification(item_id, user_id, amount)


@socketio.on("like_outfit")
def handle_like_outfit(data):
    """Handle outfit like"""
    outfit_id = data.get("outfit_id")
    user_id = data.get("user_id")

    # Broadcast to all clients in the room
    emit(
        "new_like",
        {"outfit_id": outfit_id, "user_id": user_id},
        room=f"outfit_{outfit_id}",
    )

    # Send notification to outfit owner
    notification_service.send_like_notification(outfit_id, user_id)
