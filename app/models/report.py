import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False
    )
    content_type = db.Column(
        db.String(50), nullable=False
    )  # 'item', 'fit', 'comment', etc.
    content_id = db.Column(UUID(as_uuid=True), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "reporter_id": str(self.reporter_id),
            "content_type": self.content_type,
            "content_id": str(self.content_id),
            "reason": self.reason,
            "details": self.details,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Report {self.content_type}:{self.content_id}>"
