from enum import Enum
import uuid
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class BidStatus(Enum):  # Formalized status tracking
    RESERVED = "reserved"  # Funds held via Lightning invoice
    WON = "won"  # Auction winner, invoice settled
    RELEASED = "released"  # Funds returned (outbid or auction failed)
    EXPIRED = "expired"  # Auction ended without winner


class Bid(db.Model):
    __tablename__ = "bids"  # Changed to plural for consistency

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, index=True
    )  # Renamed for clarity
    # Relationships
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    # Lightning Payment Fields
    payment_hash = db.Column(db.String(64), unique=True)  # LN invoice identifier
    hold_invoice = db.Column(db.String(512))  # Encoded invoice
    invoice_expiry = db.Column(db.DateTime)
    preimage = db.Column(db.String(64))  # For settlement proof

    encoded_invoice = db.Column(
        db.String(1024), nullable=True, unique=True
    )  # Increased length, made unique
    # Store Lightspark payment ID if this bid corresponds to an outgoing payment (e.g. for payouts)
    lightspark_payment_id = db.Column(UUID(as_uuid=True), nullable=True, unique=True)

    # Status Tracking
    status = db.Column(
        db.Enum(BidStatus), default=BidStatus.RESERVED
    )  # reserved, won, released, expire

    status_updated_at = db.Column(db.DateTime)  # Last state change

    # Expiration
    expires_at = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24), index=True
    )

    # Relationships (optimized)
    user = db.relationship("User", back_populates="bids")
    item = db.relationship("Item", back_populates="bids")

    def set_status(self, new_status: BidStatus):
        """Atomic state transition with validation"""
        valid_transitions = {
            BidStatus.RESERVED: [BidStatus.WON, BidStatus.RELEASED, BidStatus.EXPIRED],
            BidStatus.WON: [BidStatus.RELEASED],
            BidStatus.RELEASED: [],
            BidStatus.EXPIRED: [],
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")

        self.status = new_status
        self.status_updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<Bid {self.amount} on Item {self.item_id} by User {self.user_id} at {self.created_at}>"
