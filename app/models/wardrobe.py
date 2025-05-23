import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


# Association table for Wardrobe-Item many-to-many relationship
wardrobe_items = db.Table(
    "wardrobe_items",
    db.Column(
        "wardrobe_id",
        UUID(as_uuid=True),
        db.ForeignKey("wardrobes.id"),
        primary_key=True,
    ),
    db.Column(
        "item_id", UUID(as_uuid=True), db.ForeignKey("items.id"), primary_key=True
    ),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
)


class Wardrobe(db.Model):
    __tablename__ = "wardrobes"  # Changed to plural for consistency

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    name = db.Column(
        db.String(100), nullable=False, default=f"{user_id} Wardrobe"
    )  # Added a default name
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="wardrobes", lazy=True)
    items = db.relationship(
        "Item",
        secondary=wardrobe_items,
        backref=db.backref("wardrobes", lazy="dynamic"),
        lazy="dynamic",
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }

    def __repr__(self):
        return f"<Wardrobe '{self.name}' for User {self.user_id}>"
