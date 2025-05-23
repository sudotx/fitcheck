import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Fit(db.Model):
    __tablename__ = "fits"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    items = db.relationship(
        "Item",
        secondary="fit_items",
        backref=db.backref("fits", lazy="dynamic"),
        lazy="dynamic",
    )
    comments = db.relationship("Comment", backref="fit", lazy="dynamic")
    likes = db.relationship(
        "Like",
        primaryjoin="and_(Like.content_type=='fit', foreign(Like.content_id)==Fit.id)",
        lazy="dynamic",
        overlaps="likes",
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "likes_count": self.likes_count,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Fit {self.name}>"


# Association table for Fit-Item many-to-many relationship
fit_items = db.Table(
    "fit_items",
    db.Column("fit_id", UUID(as_uuid=True), db.ForeignKey("fits.id"), primary_key=True),
    db.Column(
        "item_id", UUID(as_uuid=True), db.ForeignKey("items.id"), primary_key=True
    ),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
)
