import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(160))
    profile_picture = db.Column(db.String(255))
    location = db.Column(db.String(100))
    is_celebrity = db.Column(db.Boolean, default=False)
    push_token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    items = db.relationship("Item", backref="owner", lazy=True)
    fits = db.relationship("Fit", backref="creator", lazy=True)
    notifications = db.relationship(
        "Notification", foreign_keys="Notification.user_id", backref="user", lazy=True
    )

    # Following relationships
    followers = db.relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        backref="following",
        lazy="dynamic",
    )
    following = db.relationship(
        "Follow", foreign_keys="Follow.follower_id", backref="follower", lazy="dynamic"
    )

    # Blocking relationships
    blocked_users = db.relationship(
        "Block", foreign_keys="Block.blocker_id", backref="blocker", lazy="dynamic"
    )
    blocked_by = db.relationship(
        "Block", foreign_keys="Block.blocked_id", backref="blocked", lazy="dynamic"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "bio": self.bio,
            "profile_picture": self.profile_picture,
            "location": self.location,
            "is_celebrity": self.is_celebrity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.username}>"
