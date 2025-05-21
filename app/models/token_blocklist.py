import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "jti": self.jti,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"
