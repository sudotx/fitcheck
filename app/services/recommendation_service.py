from app.models.clothing_item import ClothingItem

from app.models import Fit, Wardrobe


class RecommendationEngine:
    @staticmethod
    def recommend_outfit(user_id):
        # Simple recommendation: get user's clothing items and create a random outfit
        clothing_items = (
            ClothingItem.query.join(Wardrobe).filter(Wardrobe.user_id == user_id).all()
        )

        # Basic logic: recommend one top, one bottom, and one accessory if available
        recommended_items = {"top": None, "bottom": None, "accessory": None}

        for item in clothing_items:
            if "shirt" in item.name.lower() and not recommended_items["top"]:
                recommended_items["top"] = {"id": item.id, "name": item.name}
            elif "pants" in item.name.lower() and not recommended_items["bottom"]:
                recommended_items["bottom"] = {"id": item.id, "name": item.name}
            elif (
                "accessory" in item.name.lower() and not recommended_items["accessory"]
            ):
                recommended_items["accessory"] = {"id": item.id, "name": item.name}

        return recommended_items
