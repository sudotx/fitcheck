from enum import Enum
import uuid
from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.extensions import db


class AuctionStatus(Enum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Media fields
    image_url = db.Column(db.String(255))
    thumbnail_url = db.Column(db.String(255))
    cloudinary_public_id = db.Column(db.String(255))

    # Essential Metadata
    title = db.Column(db.String(100), nullable=False)  # Renamed from 'name'
    category = db.Column(db.String(50), index=True)  # "jacket", "dress", etc.
    dominant_colors = db.Column(ARRAY(db.String(7)))  # Hex codes for color search

    # Size System
    size_type = db.Column(db.String(20), nullable=False)  # "clothing"|"footwear"
    size_value = db.Column(db.String(20), nullable=False)  # "M", "42", "10W"
    size_compatibility = db.Column(JSON, nullable=False)  # Structured measurements
    # Example: {"waist_min": 30, "waist_max": 32, "inseam_min": 28, "length_min": 100, "length_max": 105}

    # Description
    description = db.Column(db.Text)

    # Auction Details
    auction_start_price = db.Column(db.Numeric(10, 2), nullable=False)  # Satoshis
    auction_current_bid = db.Column(db.Numeric(10, 2))  # Satoshis
    auction_ends_at = db.Column(db.DateTime, nullable=False, index=True)
    auction_status = db.Column(
        db.Enum(AuctionStatus),
        default=AuctionStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # AI/Discovery
    embedding = db.Column(ARRAY(db.Float))  # Vector for visual search
    style = db.Column(ARRAY(db.String(50)))  # For storing clothing style

    # Brand and Category
    brand = db.Column(db.String(100))  # "Nike", "Adidas", etc.
    condition = db.Column(db.String(20))  # "new", "used", "like new"
    price = db.Column(db.Numeric(10, 2))  # Satoshis
    tags = db.Column(ARRAY(db.String(50)))  # "jacket", "dress", "sneakers"
    is_public = db.Column(db.Boolean, default=True)

    # Relationships (optimized)
    user = db.relationship("User", back_populates="items")
    bids = db.relationship(
        "Bid", back_populates="item", lazy="dynamic", order_by="Bid.amount.desc()"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "size_type": self.size_type,
            "size_value": self.size_value,
            "size_compatibility": self.size_compatibility,
            "condition": self.condition,
            "price": float(self.price) if self.price else None,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_price": self.auction_current_bid or self.auction_start_price,
            "time_remaining": max(
                0, (self.auction_ends_at - datetime.utcnow()).total_seconds()
            ),
            "size": f"{self.size_value} ({self.size_type})",
            "dominant_colors": self.dominant_colors
            or [],  # Ensure dominant_colors is returned
            "style": self.style
            or [],  # New: Include style in the dictionary representation
            "auction_status": self.auction_status.value,  # Return enum value as string
            "auction_start_price": (
                float(self.auction_start_price) if self.auction_start_price else None
            ),
            "auction_current_bid": (
                float(self.auction_current_bid) if self.auction_current_bid else None
            ),
            "auction_ends_at": (
                self.auction_ends_at.isoformat() if self.auction_ends_at else None
            ),
        }

    def __repr__(self):
        return f"<Item {self.title}>"
