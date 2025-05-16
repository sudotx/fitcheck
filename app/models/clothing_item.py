from app.extensions import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY


class ClothingItem(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100))
    color = db.Column(db.String(50))
    condition = db.Column(db.String(50))
    for_sale = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float)
    tags = db.Column(ARRAY(db.String(50)))
    embedding_vector = db.Column(ARRAY(db.Float))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="clothing_items", lazy=True)

    def __repr__(self):
        return f"<ClothingItem {self.name or self.id}>"
