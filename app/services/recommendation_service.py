from datetime import datetime, timedelta
import random
from sqlalchemy import func
from app.models import ClothingItem, Wardrobe, User, db


class RecommendationEngine:
    @staticmethod
    def recommend_outfit(user_id, occasion=None, weather=None):
        """Generate personalized outfit recommendations"""
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}

        # Get user's wardrobe with size filtering
        wardrobe_items = (
            db.session.query(ClothingItem)
            .join(Wardrobe)
            .filter(
                Wardrobe.user_id == user_id,
                ClothingItem.is_clean == True,  # Only clean items
                # ClothingItem.season == get_current_season(),  # Seasonal filtering
            )
            .all()
        )

        if not wardrobe_items:
            return {"error": "No items in wardrobe"}

        # Apply recommendation strategy
        if occasion or weather:
            return RecommendationEngine._contextual_recommendation(
                wardrobe_items, user, occasion, weather
            )
        return RecommendationEngine._smart_baseline_recommendation(wardrobe_items, user)

    @staticmethod
    def _contextual_recommendation(items, user, occasion, weather):
        """Recommend based on occasion/weather"""
        filtered = [
            item
            for item in items
            if RecommendationEngine._matches_context(item, occasion, weather)
        ]

        if not filtered:
            filtered = items  # Fallback to all items

        return RecommendationEngine._smart_baseline_recommendation(filtered, user)

    @staticmethod
    def _matches_context(item, occasion, weather):
        """Check if item matches usage context"""
        rules = {
            "formal": lambda x: x.formality_rating >= 4,
            "casual": lambda x: x.formality_rating <= 2,
            "rainy": lambda x: x.water_resistant,
            "cold": lambda x: x.warmth_rating >= 3,
        }

        checks = []
        if occasion:
            checks.append(rules.get(occasion, lambda x: True))
        if weather:
            checks.append(rules.get(weather, lambda x: True))

        return all(check(item) for check in checks)

    @staticmethod
    def _smart_baseline_recommendation(items, user):
        """Core recommendation logic"""
        # Group by category using actual item types
        categorized = {
            "tops": [],
            "bottoms": [],
            "outerwear": [],
            "accessories": [],
            "shoes": [],
        }

        # for item in items:
        #     if item.category in categorized:
        #         categorized[item.category].append(item)
        #     elif item.item_type:  # Fallback to type detection
        #         detected = detect_category(item)
        #         if detected in categorized:
        #             categorized[detected].append(item)

        # Apply color coordination
        color_palette = RecommendationEngine._extract_color_preferences(user, items)

        # Select items
        selection = {
            "top": RecommendationEngine._select_item(
                categorized["tops"], color_palette
            ),
            "bottom": RecommendationEngine._select_item(
                categorized["bottoms"], color_palette
            ),
            "shoes": RecommendationEngine._select_item(
                categorized["shoes"], color_palette
            ),
            "accessories": RecommendationEngine._select_accessories(
                categorized["accessories"], color_palette
            ),
        }

        # Add metadata
        return {
            "outfit": {k: v.to_dict() if v else None for k, v in selection.items()},
            "confidence": random.uniform(0.7, 0.9),  # Mock confidence score
            "color_palette": color_palette,
            "generated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _extract_color_preferences(user, items):
        """Determine user's preferred color schemes"""
        # Simple implementation - extend with AI later
        color_counts = {}
        for item in items:
            for color in item.colors:
                color_counts[color] = color_counts.get(color, 0) + 1

        return sorted(color_counts.keys(), key=lambda x: -color_counts[x])[:3]

    @staticmethod
    def _select_item(candidates, color_palette):
        """Select best matching item from category"""
        if not candidates:
            return None

        # Simple scoring - enhance with embeddings later
        scored = []
        for item in candidates:
            score = 0
            if any(c in color_palette for c in item.colors):
                score += 2
            if item.last_worn < datetime.utcnow() - timedelta(days=7):
                score += 1
            scored.append((score, item))

        return (
            max(scored, key=lambda x: x[0])[1] if scored else random.choice(candidates)
        )

    @staticmethod
    def _select_accessories(candidates, color_palette):
        """Select 1-2 accessories"""
        if not candidates:
            return []

        accessories = [
            acc for acc in candidates if any(c in color_palette for c in acc.colors)
        ][:2]

        return (
            accessories
            if accessories
            else random.sample(candidates, min(2, len(candidates)))
        )
