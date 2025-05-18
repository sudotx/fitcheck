import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'item' or 'fit'
    content_id = db.Column(UUID(as_uuid=True), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "content_type", "content_id", name="unique_like"
        ),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "content_type": self.content_type,
            "content_id": str(self.content_id),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Like {self.content_type}:{self.content_id}>"
