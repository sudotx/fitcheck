import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.extensions import db


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    brand = db.Column(db.String(100))
    color = db.Column(db.String(50))
    size = db.Column(db.String(20))
    condition = db.Column(db.String(20))
    price = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(255))
    thumbnail_url = db.Column(db.String(255))
    cloudinary_public_id = db.Column(db.String(255))
    tags = db.Column(ARRAY(db.String(50)))
    embedding = db.Column(ARRAY(db.Float))
    is_public = db.Column(db.Boolean, default=True)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    likes = db.relationship(
        "Like",
        primaryjoin="and_(Like.content_type=='item', foreign(Like.content_id)==Item.id)",
        lazy="dynamic",
        overlaps="likes",
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "color": self.color,
            "size": self.size,
            "condition": self.condition,
            "price": float(self.price) if self.price else None,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "is_public": self.is_public,
            "likes_count": self.likes_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Item {self.name}>"
