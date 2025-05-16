from app.extensions import db


class Wardrobe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # This will now refer to the updated back reference name
    items = db.relationship("ClothingItem", backref="wardrobe", lazy=True)
