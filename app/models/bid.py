# app/models/bid.py
from app.extensions import db


class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationship back to User
    user = db.relationship(
        "User", back_populates="bids"
    )  # Assuming you will add bids to User
