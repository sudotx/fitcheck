import os
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
import numpy as np
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import config
from app.extensions import db
from app.models.clothing_item import Item


class AIService:
    """
    Service class for AI-powered image processing and recommendations using Gemini and LangChain.
    """

    def __init__(self):
        """
        Initializes the AI Service, configuring Gemini API access and LangChain models.
        """
        try:
            genai.configure(api_key=config.GOOGLE_API_KEY)
        except AttributeError:
            print(
                "Warning: GOOGLE_API_KEY not found in config. Please set it for AI services to work."
            )

        self.vision_llm = ChatGoogleGenerativeAI(
            model="gemini-pro-vision",
            google_api_key=config.GOOGLE_API_KEY,
        )

        # Initialize an in-memory FAISS vector store.
        # In a production environment, you would persist and load this index.
        # It's initialized to None and created on demand when the first embedding is added.
        self.faiss_vector_store = None

    def _initialize_faiss_if_needed(self, embedding_dimension: int = 768):
        """
        Initializes the FAISS vector store if it hasn't been already.
        A dummy embedding is used to create the initial index structure.
        """
        if self.faiss_vector_store is None:
            print(
                f"Initializing FAISS vector store with dimension {embedding_dimension}..."
            )
            # FAISS needs an initial vector to determine its dimension.
            # We create a dummy embedding and use LangChain's FAISS.from_embeddings.
            # Note: For actual embedding generation for the FAISS store, we'll use genai.embed_content.
            # This embedding is just to initialize the LangChain wrapper correctly.
            dummy_embedding_model = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=config.GOOGLE_API_KEY,  # Or os.environ.get("GOOGLE_API_KEY")
            )
            # Create a dummy index with a single dummy vector
            self.faiss_vector_store = FAISS.from_embeddings(
                text_embeddings=[
                    ("dummy_id", np.random.rand(embedding_dimension).tolist())
                ],
                embedding=dummy_embedding_model,
            )
            print("FAISS vector store initialized.")

    def generate_embedding(self, image_url: str) -> List[float]:
        """
        Generates a numerical embedding vector for an image using Gemini's embedding model.
        The embedding can be used for similarity searches.

        Args:
            image_url (str): The URL of the image to generate the embedding for.

        Returns:
            List[float]: The generated embedding vector as a list of floats.
                         Returns an empty list if an error occurs.
        """
        try:
            # Use genai.embed_content for robust multimodal embedding generation.
            # 'models/embedding-001' is suitable for various embedding tasks.
            # The 'task_type' helps in optimizing the embedding for specific use cases (e.g., retrieval).
            response = genai.embed_content(
                model="models/embedding-001",
                content={"parts": [{"image_uri": image_url}]},
                task_type="RETRIEVAL_DOCUMENT",  # Suitable for similarity searches
            )
            embedding = response["embedding"]
            print(
                f"Successfully generated embedding of length {len(embedding)} for {image_url}"
            )
            return embedding
        except Exception as e:
            print(f"Error generating embedding for {image_url}: {e}")
            return []  # Return an empty list on failure

    def generate_colors(self, image_url: str) -> List[str]:
        """
        Identifies and lists the dominant colors present in an image using Gemini-Pro-Vision.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of dominant color names (e.g., ["red", "blue", "green"]).
                       Returns an empty list if an error occurs.
        """
        try:
            # Define a prompt template to guide the LLM in extracting colors.
            prompt = "What are the main dominant colors in this image? List them as a concise, comma-separated list. Example: red, blue, green"

            # Prepare the content for the vision model, combining text prompt and image URI.
            parts = [{"text": prompt}, {"image_uri": image_url}]

            # Invoke the LangChain LLM to get the response.
            response = self.vision_llm.invoke(parts)
            colors_str = response.content
            # Split the string by comma and clean up each color name.
            colors = [c.strip().lower() for c in colors_str.split(",") if c.strip()]
            print(f"Generated colors for {image_url}: {colors}")
            return colors
        except Exception as e:
            print(f"Error generating colors for {image_url}: {e}")
            return []

    def get_clothing_style(self, image_url: str) -> List[str]:
        """
        Determines clothing style using LLMChain for more detailed analysis.
        """
        try:
            # Create a prompt template for style analysis
            style_prompt = PromptTemplate(
                input_variables=["image_url"],
                template="""
                Analyze the clothing style in this image: {image_url}
                
                Consider the following aspects:
                1. Overall aesthetic (e.g., bohemian, minimalist, classic)
                2. Cultural influences (e.g., western, eastern, urban)
                3. Fashion era (e.g., vintage, modern, futuristic)
                
                Provide a detailed analysis and return the top 3 most relevant style terms.
                """,
            )

            # Create an LLMChain for style analysis
            style_chain = LLMChain(llm=self.vision_llm, prompt=style_prompt)

            # Execute the chain
            styles_str = style_chain.run(image_url=image_url)
            styles = [s.strip().lower() for s in styles_str.split(",") if s.strip()]

            return styles
        except Exception as e:
            print(f"Error analyzing clothing style: {e}")
            return []

    def generate_tags(self, image_url: str) -> List[str]:
        """
        Generates descriptive tags using LLMChain for more structured output.
        """
        try:
            # Create a prompt template for tag generation
            tag_prompt = PromptTemplate(
                input_variables=["image_url"],
                template="""
                Analyze this clothing item image: {image_url}
                
                Generate tags in the following categories:
                1. Item Type (e.g., t-shirt, dress, pants)
                2. Material (e.g., cotton, wool, silk)
                3. Pattern (e.g., striped, floral, solid)
                4. Occasion (e.g., casual, formal, sport)
                5. Season (e.g., summer, winter, all-season)
                
                Return the tags as a comma-separated list.
                """,
            )

            # Create an LLMChain for tag generation
            tag_chain = LLMChain(llm=self.vision_llm, prompt=tag_prompt)

            # Execute the chain
            tags_str = tag_chain.run(image_url=image_url)
            tags = [tag.strip().lower() for tag in tags_str.split(",") if tag.strip()]

            return tags
        except Exception as e:
            print(f"Error generating tags: {e}")
            return []

    def add_to_index(self, embedding: List[float], item_id: str):
        """
        Adds an item's embedding to the FAISS vector store for similarity search.
        Initializes the FAISS store if it's not already initialized.

        Args:
            embedding (List[float]): The embedding vector of the item.
            item_id (str): The unique identifier for the item.
        """
        try:
            # Ensure FAISS is initialized before adding.
            self._initialize_faiss_if_needed(embedding_dimension=len(embedding))

            # When adding to FAISS, we use the item_id as the 'text' content
            # since we're primarily storing embeddings associated with IDs.
            # The LangChain FAISS wrapper handles mapping embeddings to text content.
            self.faiss_vector_store.add_texts(texts=[item_id], embeddings=[embedding])
            print(f"Successfully added item {item_id} to FAISS index.")
        except Exception as e:
            print(f"Error adding item {item_id} to FAISS index: {e}")

    def find_similar_items(self, item_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Finds items similar to a given item based on their embeddings using FAISS.

        Args:
            item_id (str): The ID of the item for which to find similar items.
            limit (int): The maximum number of similar items to return.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a
                                   similar item. Returns an empty list if no similar items
                                   are found or an error occurs.
        """
        try:
            # Check if the FAISS store is initialized.
            if self.faiss_vector_store is None:
                print("FAISS vector store not initialized. Cannot find similar items.")
                return []

            # Retrieve the target item and its embedding from the database.
            target_item = Item.query.get(item_id)
            if not target_item or not target_item.embedding:
                print(f"Item {item_id} not found or has no embedding.")
                return []

            query_embedding = target_item.embedding

            # Perform similarity search using the target item's embedding.
            # We ask for `limit + 1` results because the item itself will be the most similar.
            docs_with_scores = self.faiss_vector_store.similarity_search_by_vector(
                embedding=query_embedding, k=limit + 1
            )

            similar_item_ids = []
            for doc, score in docs_with_scores:
                # Exclude the queried item itself from the results.
                if doc.page_content != item_id:
                    similar_item_ids.append(doc.page_content)
                    if len(similar_item_ids) >= limit:
                        break  # Stop if we have enough similar items

            # Fetch the full item details from the database using the retrieved IDs.
            similar_items_from_db = Item.query.filter(
                Item.id.in_(similar_item_ids)
            ).all()
            return [item.to_dict() for item in similar_items_from_db]

        except Exception as e:
            print(f"Error finding similar items for {item_id}: {e}")
            return []

    def get_tag_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Retrieves tag suggestions from the database based on a query string.

        Args:
            query (str): The search query to filter tags.
            limit (int): The maximum number of suggestions to return.

        Returns:
            List[str]: A list of suggested tags.
        """
        try:
            # Query the database for all unique tags.
            tag_results = db.session.query(Item.tags).distinct().all()

            # Flatten the list of lists into a single list of tags and filter out None values.
            all_tags = []
            for tags_tuple in tag_results:
                if tags_tuple[0] is not None:
                    all_tags.extend(tags_tuple[0])

            # Filter tags that contain the query string (case-insensitive).
            suggestions = [tag for tag in all_tags if query.lower() in tag.lower()]

            # Remove duplicate suggestions while preserving their order.
            seen = set()
            suggestions = [
                tag for tag in suggestions if not (tag in seen or seen.add(tag))
            ]

            # Return the top N suggestions based on the limit.
            return suggestions[:limit]
        except Exception as e:
            print(f"Error getting tag suggestions: {e}")
            return []

    def recommend_outfit(self, user_id: str) -> Dict[str, Any]:
        """
        Recommends an outfit based on a user's items and preferences using LLMChain.
        """
        try:
            # Get user's items and preferences
            user_items = Item.query.filter_by(user_id=user_id).all()

            # Create a prompt template for outfit recommendations
            outfit_prompt = PromptTemplate(
                input_variables=["user_items", "season", "occasion"],
                template="""
                Based on the following clothing items:
                {user_items}
                
                Recommend a complete outfit for {season} season and {occasion} occasion.
                Consider color coordination, style matching, and seasonal appropriateness.
                Return the recommendation in a structured format.
                """,
            )

            # Create an LLMChain for outfit recommendations
            outfit_chain = LLMChain(llm=self.vision_llm, prompt=outfit_prompt)

            # Execute the chain
            recommendation = outfit_chain.run(
                user_items=str([item.to_dict() for item in user_items]),
                season="current",  # You could get this from user preferences or system
                occasion="casual",  # You could get this from user preferences
            )

            return recommendation
        except Exception as e:
            print(f"Error generating outfit recommendation: {e}")
            return {}

    def get_recommendations(
        self, user_id: str, page: int = 1, per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Provides personalized item recommendations for a user with pagination.
        (Currently returns public items as a placeholder, needs actual recommendation algorithm).

        Args:
            user_id (str): The ID of the user.
            page (int): The page number for pagination.
            per_page (int): The number of items per page.

        Returns:
            Dict[str, Any]: A dictionary containing paginated results and metadata about the recommendations.
        """
        # TODO: Implement actual personalized recommendation algorithm.
        # This could involve collaborative filtering, content-based filtering,
        # or hybrid approaches using embeddings and user history.
        print(
            f"Getting placeholder recommendations for user {user_id}, page {page}, per_page {per_page}"
        )
        # For now, it returns paginated public items.
        query = Item.query.filter(Item.is_public == True)

        pagination = query.paginate(page=page, per_page=per_page)

        return {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }


# Create a singleton instance of the AIService.
# This ensures that only one instance of the service is used throughout the application.
ai_service = AIService()
