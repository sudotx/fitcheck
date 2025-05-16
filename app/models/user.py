from app.extensions import db
from datetime import datetime
from app.models.wardrobe import Wardrobe
from app.models.fit import Fit  # Assuming Fit is another model you will define


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_celebrity = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wardrobes = db.relationship("Wardrobe", backref="user", lazy=True)
    fits = db.relationship(
        "Fit", backref="fitted_by", lazy=True
    )  # Updated backref name
