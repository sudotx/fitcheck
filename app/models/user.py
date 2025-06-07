import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.user_privacy import UserPrivacy


class UserStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNVERIFIED = "unverified"


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.UNVERIFIED)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)

    password_hash = db.Column(db.String(255), nullable=False)

    totp_secret = db.Column(db.String(255))
    totp_enabled = db.Column(db.Boolean, default=False)
    totp_verified = db.Column(db.Boolean, default=False)
    totp_verified_at = db.Column(db.DateTime)

    email = db.Column(db.String(255), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    is_celebrity = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Marketplace Specific
    lightning_address = db.Column(db.String(255), unique=True, index=True)
    seller_rating = db.Column(db.Float, default=0.0)
    payout_hold = db.Column(db.Boolean, default=True)  # For new sellers
    completed_sales = db.Column(db.Integer, default=0)

    temp_balance_hold = db.Column(db.Float, default=0.0)

    # New size preference fields
    body_type = db.Column(db.String(20))  # apple/pear/rectangle
    measurements = db.Column(JSON)  # Store measurements
    preferred_size_system = db.Column(db.String(2))  # US, EU, UK

    # Lightning wallet
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    items = db.relationship("Item", backref="owner", lazy=True)
    fits = db.relationship("Fit", backref="creator", lazy=True)
    bids = db.relationship("Bid", backref="bidder", lazy=True)
    notifications = db.relationship(
        "Notification", foreign_keys="Notification.user_id", backref="user", lazy=True
    )

    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    login_attempts = db.Column(db.Integer, default=0)

    def authenticate(self, password=None, lnurl_auth=None):
        """Flexible auth supporting both methods"""
        if password and check_password_hash(self.password_hash, password):
            return True
        if lnurl_auth and lnurl_auth == self.lightning_address:
            return True
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_privacy_data(self):
        """Get user's privacy data from MongoDB"""
        return UserPrivacy.get_by_user_id(self.id)

    def update_privacy_data(self, **kwargs):
        """Update user's privacy data in MongoDB"""
        privacy_data = self.get_privacy_data()
        if privacy_data:
            return UserPrivacy(**privacy_data).update(**kwargs)
        return UserPrivacy.create(user_id=self.id, **kwargs)

    def get_size_preferences(self):
        """Returns non-PII size data safe for public sharing"""
        return {"system": self.preferred_size_system, "body_type": self.body_type}

    def to_dict(self):
        """Convert user to dictionary, excluding sensitive data"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "email_verified": self.email_verified,
            "is_celebrity": self.is_celebrity,
            "lightning_address": self.lightning_address,
            "seller_rating": round(self.seller_rating, 1),
            "completed_sales": self.completed_sales,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "role": self.role.value,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_attempts": self.login_attempts,
            "totp_enabled": self.totp_enabled,
            "totp_verified": self.totp_verified,
            "totp_verified_at": (
                self.totp_verified_at.isoformat() if self.totp_verified_at else None
            ),
            "seller_rating": round(self.seller_rating, 1),
            "payout_hold": self.payout_hold,
            "completed_sales": self.completed_sales,
        }

    def __repr__(self):
        return f"<User {self.username}>"
