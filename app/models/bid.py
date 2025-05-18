import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Bid(db.Model):
    __tablename__ = "bid"  # Explicitly set table name

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("item.id"), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="bids", lazy=True)
    item = db.relationship("Item", backref="bids", lazy=True)

    def __repr__(self):
        return f"<Bid {self.amount} on Item {self.item_id} by User {self.user_id} at {self.timestamp}>"
