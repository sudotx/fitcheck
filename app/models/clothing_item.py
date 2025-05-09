from app.extensions import db


class ClothingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    wardrobe_id = db.Column(db.Integer, db.ForeignKey("wardrobe.id"), nullable=False)

    # Relationship back to Wardrobe
    wardrobe = db.relationship("Wardrobe", backref="items")
