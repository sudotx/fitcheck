import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Follow(db.Model):
    __tablename__ = "follows"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False
    )
    following_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("follower_id", "following_id", name="unique_follow"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "follower_id": str(self.follower_id),
            "following_id": str(self.following_id),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.following_id}>"
