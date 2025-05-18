import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Block(db.Model):
    __tablename__ = "blocks"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False
    )
    blocked_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("blocker_id", "blocked_id", name="unique_block"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "blocker_id": str(self.blocker_id),
            "blocked_id": str(self.blocked_id),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Block {self.blocker_id} -> {self.blocked_id}>"
