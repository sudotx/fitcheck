from app.extensions import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class Wardrobe(db.Model):
    __tablename__ = "wardrobe"  # Explicitly set table name

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    name = db.Column(
        db.String(100), nullable=False, default="My Wardrobe"
    )  # Added a default name
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="wardrobes", lazy=True)
    items = db.relationship(
        "Item", backref="wardrobe", lazy=True
    )  # Assuming a Wardrobe can contain multiple Items

    def __repr__(self):
        return f"<Wardrobe '{self.name}' for User {self.user_id}>"
