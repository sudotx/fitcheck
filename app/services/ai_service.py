# import os
# from typing import List, Tuple

# import google.generativeai as genai
# from langchain.chains import LLMChain
# from langchain.prompts import PromptTemplate
# from langchain.vectorstores import FAISS
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# from ..config import config
# from ..extensions import db
# from ..models import Item

from typing import List, Dict, Any
import numpy as np
from app.models.clothing_item import Item
from app.extensions import db, celery


class AIService:
    def __init__(self):
        # Initialize any AI models or services here
        pass

    def generate_embedding(self, image) -> np.ndarray:
        """Generate embedding vector for an image"""
        # TODO: Implement actual embedding generation
        # For now, return a random vector
        return np.random.rand(512)

    def generate_tags(self, image) -> List[str]:
        """Generate tags for an image"""
        # TODO: Implement actual tag generation
        # For now, return some default tags
        return ["casual", "summer"]

    def get_tag_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get tag suggestions based on a query string

        Args:
            query (str): The search query
            limit (int): Maximum number of suggestions to return

        Returns:
            List[str]: List of suggested tags
        """
        try:
            # Get all unique tags from items
            tag_results = db.session.query(Item.tags).distinct().all()

            # Flatten the list of tags and filter out None values
            all_tags = []
            for tags_tuple in tag_results:
                if tags_tuple[0] is not None:  # Check if tags exist
                    all_tags.extend(tags_tuple[0])

            # Filter tags that contain the query (case-insensitive)
            suggestions = [tag for tag in all_tags if query.lower() in tag.lower()]

            # Remove duplicates while preserving order
            seen = set()
            suggestions = [
                tag for tag in suggestions if not (tag in seen or seen.add(tag))
            ]

            # Return top N suggestions
            return suggestions[:limit]
        except Exception as e:
            # Log the error and return empty list
            print(f"Error getting tag suggestions: {str(e)}")
            return []

    def find_similar_items(self, item_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar items based on embedding vectors"""
        # TODO: Implement actual similarity search
        # For now, return random items
        items = Item.query.filter(Item.id != item_id).limit(limit).all()
        return [item.to_dict() for item in items]

    def recommend_outfit(self, user_id: str) -> Dict[str, Any]:
        """Recommend an outfit based on user's items and preferences"""
        # TODO: Implement actual outfit recommendation
        # For now, return random items
        items = Item.query.limit(3).all()
        return {
            "top": items[0].to_dict() if len(items) > 0 else None,
            "bottom": items[1].to_dict() if len(items) > 1 else None,
            "accessory": items[2].to_dict() if len(items) > 2 else None,
        }

    def get_recommendations(
        self, user_id: str, page: int = 1, per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get personalized item recommendations for a user

        Args:
            user_id (str): The ID of the user
            page (int): Page number for pagination
            per_page (int): Number of items per page

        Returns:
            Dict[str, Any]: Dictionary containing paginated results and metadata
        """
        # TODO: Implement actual recommendation algorithm
        # For now, return random items that are public
        query = Item.query.filter(Item.is_public == True)

        # Get paginated results
        pagination = query.paginate(page=page, per_page=per_page)

        return {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }


# Create singleton instance
ai_service = AIService()


@celery.task
def generate_item_embedding(item_id: str) -> None:
    """
    Celery task to generate and store embedding for an item

    Args:
        item_id (str): The ID of the item to generate embedding for
    """
    try:
        # Get the item
        item = Item.query.get(item_id)
        if not item:
            print(f"Item {item_id} not found")
            return

        # Generate embedding using the image URL
        embedding = ai_service.generate_embedding(item.image_url)

        # Store the embedding
        item.embedding = embedding
        db.session.commit()
        print(f"Generated embedding for item {item_id}")
    except Exception as e:
        print(f"Error generating embedding for item {item_id}: {str(e)}")
        db.session.rollback()


@celery.task
def generate_item_tags(item_id: str) -> None:
    """
    Celery task to generate and store tags for an item

    Args:
        item_id (str): The ID of the item to generate tags for
    """
    try:
        # Get the item
        item = Item.query.get(item_id)
        if not item:
            print(f"Item {item_id} not found")
            return

        # Generate tags using the image URL
        tags = ai_service.generate_tags(item.image_url)

        # Store the tags
        item.tags = tags
        db.session.commit()
        print(f"Generated tags for item {item_id}: {tags}")
    except Exception as e:
        print(f"Error generating tags for item {item_id}: {str(e)}")
        db.session.rollback()


# def generate_item_embedding(item_id: str):
#     """Generate and store embedding for an item"""
#     item = Item.query.get(item_id)
#     if not item:
#         return

#     # Generate embedding using the image URL
#     embedding = ai_service.generate_embedding(item.image_url)

#     # Store the embedding
#     item.embedding = embedding
#     db.session.commit()

#     # Add to vector store for similarity search
#     ai_service.add_to_index(embedding, str(item_id))


# def generate_item_tags(item_id: str):
#     """Generate and store tags for an item"""
#     item = Item.query.get(item_id)
#     if not item:
#         return

#     # Generate tags using the image URL
#     tags = ai_service.generate_tags(item.image_url)

#     # Store the tags
#     item.tags = tags
#     db.session.commit()
