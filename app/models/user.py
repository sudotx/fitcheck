from app.extensions import db
from datetime import datetime
from app.models.wardrobe import Wardrobe
from app.models.fit import Fit  # Assuming Fit is another model you will define
import uuid
from sqlalchemy.dialects.postgresql import UUID


class User(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    bio = db.Column(db.String(160))  # Increased length to be more useful
    avatar_url = db.Column(db.String(255))  # Increased length for URLs
    followers = db.Column(db.ARRAY(UUID(as_uuid=True)))
    following = db.Column(db.ARRAY(UUID(as_uuid=True)))
    is_celebrity = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wardrobes = db.relationship("Wardrobe", backref="user", lazy=True)
    fits = db.relationship(
        "Fit", backref="fitted_by", lazy=True
    )  # Updated backref name

    def __repr__(self):
        return f"<User {self.username}>"
