import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'like', 'comment', 'follow', etc.
    content_type = db.Column(
        db.String(50), nullable=False
    )  # 'item', 'fit', 'comment', etc.
    content_id = db.Column(UUID(as_uuid=True), nullable=False)
    actor_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "type": self.type,
            "content_type": self.content_type,
            "content_id": str(self.content_id),
            "actor_id": str(self.actor_id),
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Notification {self.type} for {self.user_id}>"
