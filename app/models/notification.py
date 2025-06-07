import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class NotificationType(Enum):
    BID_RECEIVED = "bid_received"
    BID_OUTBID = "bid_outbid"
    AUCTION_WON = "auction_won"
    AUCTION_EXPIRED = "auction_expired"
    SIZE_RESTOCK = "size_restock"  # For saved searches
    SYSTEM_MESSAGE = "system_message"
    MARKETPLACE_MESSAGE = "marketplace_message"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    item_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("items.id"),
        nullable=True,  # Some notifications won't link to items
    )
    actor_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,  # System-generated notifs won't have an actor
    )

    notification_data = db.Column(JSON, nullable=True)

    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, index=True  # For sorting
    )

    user = db.relationship("User", foreign_keys=[user_id])
    item = db.relationship("Item")
    actor = db.relationship("User", foreign_keys=[actor_id])

    def to_dict(self):
        base = {
            "id": str(self.id),
            "type": self.type.value,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "preview": self._generate_preview(),
        }

        if self.item_id:
            base["item"] = {
                "id": str(self.item_id),
                "title": self.item.title if self.item else "[Deleted]",
                "image": self.item.images[0] if self.item else None,
            }

        if self.actor_id:
            base["actor"] = {
                "id": str(self.actor_id),
                "username": self.actor.username if self.actor else "[Deleted]",
            }

        return base

    def _generate_preview(self):
        previews = {
            NotificationType.BID_RECEIVED: "New bid on your item",
            NotificationType.BID_OUTBID: "You've been outbid",
            NotificationType.AUCTION_WON: "You won the auction!",
            NotificationType.AUCTION_EXPIRED: "Your auction ended unsold",
            NotificationType.SIZE_RESTOCK: "New items in your size",
        }
        return previews.get(self.type, "New notification")

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            db.session.commit()

    def __repr__(self):
        return f"<Notification {self.type} for {self.user_id}>"
