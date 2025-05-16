from app.extensions import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY


class Fit(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    item_ids = db.Column(ARRAY(UUID(as_uuid=True)))
    likes = db.Column(ARRAY(UUID(as_uuid=True)))
    comments = db.Column(db.ARRAY(db.JSON))  # Assuming comments will be stored as JSON objects
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="outfits", lazy=True)

    def __repr__(self):
        return f"<Outfit {self.title or self.id}>"