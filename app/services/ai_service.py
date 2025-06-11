from typing import Any, Dict, List, Optional
import numpy as np

# Import necessary components for Tools
from langchain.tools import tool, StructuredTool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import config
from app.extensions import db
from app.models.clothing_item import Item

from google import genai


class AIService:
    """
    Service class for AI-powered image processing and fashion recommendations using Gemini and LangChain.
    Integrates agentic capabilities for more complex queries.
    """

    def __init__(self):
        """
        Initializes the AI Service, configuring Gemini API access and LangChain models.
        """
        try:
            self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
        except AttributeError:
            print(
                "Warning: GOOGLE_API_KEY not found in config. Please set it for AI services to work."
            )

        self.vision_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview",
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.4,  # Lower temperature for more focused, less creative outputs
        )
        self.text_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview",
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.4,  # Good for reasoning and tool selection
        )

        # Initialize the agent with access to the tools defined below
        self.agent_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview",
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.3,  # Slightly lower temperature for more predictable tool selection
        )
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> List[Any]:
        """
        Registers methods of this class as tools for the agent.
        """
        # Registering methods as tools using LangChain's @tool decorator
        # For methods requiring image_url, we'll wrap them in StructuredTool for explicit arguments.
        # This allows the agent to understand what arguments each tool expects.

        @tool
        def generate_colors_tool(image_url: str) -> List[str]:
            """Identifies and lists the dominant colors present in the clothing items in an image."""
            return self.generate_colors(image_url)

        @tool
        def get_clothing_style_tool(image_url: str) -> List[str]:
            """Determines the overall clothing style present in an image."""
            return self.get_clothing_style(image_url)

        @tool
        def detect_objects_in_image_tool(image_url: str) -> List[str]:
            """Detects prominent objects within an image, with a focus on clothing and accessories."""
            return self.detect_objects_in_image(image_url)

        @tool
        def segment_image_for_clothing_tool(image_url: str) -> List[str]:
            """Semantically segments and describes individual clothing parts worn by a person in an image."""
            return self.segment_image_for_clothing(image_url)

        @tool
        def get_clothing_vibe_tool(image_url: str) -> List[str]:
            """Determines the overall vibe or mood conveyed by the clothing in an image."""
            return self.get_clothing_vibe(image_url)

        @tool
        def generate_tags_tool(image_url: str) -> List[str]:
            """Generates descriptive tags for a clothing item (or main outfit) in an image."""
            return self.generate_tags(image_url)

        # Note: generate_embedding is typically used internally for similarity search,
        # not usually called directly by a high-level agent. Keeping it internal for now.

        @tool
        def get_tag_suggestions_tool(query: str, limit: int = 10) -> List[str]:
            """Retrieves tag suggestions from the database based on a search query string."""
            return self.get_tag_suggestions(query, limit)

        # For recommend_outfit, we need more context than just image_url, linking to user_id
        # This tool would ideally be called by an agent that has access to user context.
        # For simplicity, let's keep it as a direct method for now, or define a more complex tool input.
        # @tool
        # def recommend_outfit_tool(user_id: str, season: str = "current", occasion: str = "casual") -> Dict[str, Any]:
        #     """Recommends a complete outfit based on a user's available items and specified season/occasion."""
        #     return self.recommend_outfit(user_id, season, occasion)

        # The agent itself will be built in `process_fashion_query_with_agent`
        # and will use these tools.
        return [
            generate_colors_tool,
            get_clothing_style_tool,
            detect_objects_in_image_tool,
            segment_image_for_clothing_tool,
            get_clothing_vibe_tool,
            generate_tags_tool,
            get_tag_suggestions_tool,
            # If recommend_outfit needs to be an agent tool, it requires careful input definition
            # for the agent to understand how to call it.
        ]

    def generate_embedding(self, image_url: str) -> List[float]:
        """
        Generates a numerical embedding vector for an image using Gemini's embedding model.
        This method is kept as embeddings can be useful for other purposes even without FAISS,
        e.g., for direct comparison within the application logic.

        Args:
            image_url (str): The URL of the image to generate the embedding for.

        Returns:
            List[float]: The generated embedding vector as a list of floats.
                         Returns an empty list if an error occurs.
        """
        try:
            response = self.client.embed_content(
                model="models/embedding-001",
                content={"parts": [{"image_uri": image_url}]},
                task_type="RETRIEVAL_DOCUMENT",
            )
            embedding = response["embedding"]
            print(
                f"Successfully generated embedding of length {len(embedding)} for {image_url}"
            )
            return embedding
        except Exception as e:
            print(f"Error generating embedding for {image_url}: {e}")
            return []

    def generate_colors(self, image_url: str) -> List[str]:
        """
        Identifies and lists the dominant colors present in the clothing items in an image
        using Gemini-Pro-Vision.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of dominant color names (e.g., ["red", "blue", "green"]).
                       Returns an empty list if an error occurs.
        """
        try:
            # Optimized Prompt
            prompt = "Analyze the clothing in this image. What are the dominant colors of the **clothing items**? List them as a concise, comma-separated list of common color names. Example: `navy blue, forest green, off-white`"
            parts = [{"text": prompt}, {"image_uri": image_url}]
            response = self.vision_llm.invoke(parts)
            colors_str = response.content
            colors = [c.strip().lower() for c in colors_str.split(",") if c.strip()]
            print(f"Generated colors for {image_url}: {colors}")
            return colors
        except Exception as e:
            print(f"Error generating colors for {image_url}: {e}")
            return []

    def get_clothing_style(self, image_url: str) -> List[str]:
        """
        Determines the overall clothing style present in an image using Gemini-Pro-Vision.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of clothing style terms (e.g., ["bohemian", "vintage", "streetwear"]).
                       Returns an empty list if an error occurs.
        """
        try:
            # Optimized Prompt
            style_prompt = PromptTemplate(
                input_variables=["image_url"],
                template="""
                As a **professional fashion stylist**, analyze the overall **clothing style** of the person(s) in this image: `{image_url}`.
                Consider:
                * **Overall Aesthetic**: bohemian, minimalist, classic, casual, formal, sporty, avant-garde, streetwear, vintage.
                * **Cultural/Historical Influences**: e.g., 70s retro, 90s grunge, urban, preppy.
                * **Key Style Elements**: typical fabrics, silhouettes, accessories, common color palettes.
                Provide **3-5 most relevant style terms**, comma-separated. Prioritize the most prominent styles. Example: `streetwear, urban, casual, athleisure, modern`
                """,
            )
            style_chain = LLMChain(llm=self.vision_llm, prompt=style_prompt)
            styles_str = style_chain.run(image_url=image_url)
            styles = [s.strip().lower() for s in styles_str.split(",") if s.strip()]
            print(f"Identified styles for {image_url}: {styles}")
            return styles
        except Exception as e:
            print(f"Error analyzing clothing style for {image_url}: {e}")
            return []

    def detect_objects_in_image(self, image_url: str) -> List[str]:
        """
        Detects prominent objects within an image using Gemini-Pro-Vision, with a focus on clothing.
        Note: Gemini-Pro-Vision primarily provides descriptive detection.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of detected objects (e.g., ["person", "t-shirt", "jeans", "shoes"]).
                       Returns an empty list if an error occurs.
        """
        try:
            # Optimized Prompt
            prompt = """
            List **only** the distinct **clothing items and accessories** worn by the person(s) in this image, in a concise, comma-separated list. Do not include people or background objects. Example: `t-shirt, denim jacket, jeans, sneakers, backpack`
            """
            parts = [{"text": prompt}, {"image_uri": image_url}]
            response = self.vision_llm.invoke(parts)
            detected_objects_str = response.content
            detected_objects = [
                obj.strip().lower()
                for obj in detected_objects_str.split(",")
                if obj.strip()
            ]
            print(f"Detected objects in {image_url}: {detected_objects}")
            return detected_objects
        except Exception as e:
            print(f"Error detecting objects in {image_url}: {e}")
            return []

    def segment_image_for_clothing(self, image_url: str) -> List[str]:
        """
        Semantically segments and describes individual clothing parts worn by a person in an image.
        This aims to "single out the parts of the cloth" by describing them in detail.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of detailed descriptions for each clothing part identified
                       (e.g., "a dark blue denim jacket", "a white crew-neck t-shirt", "black skinny jeans").
                       Returns an empty list if an error occurs.
        """
        try:
            # Optimized Prompt
            prompt = """
            As an **expert fashion analyst**, meticulously describe **each distinct piece of clothing** a person is wearing in this image. For every item, provide a detailed, concise description covering its: **type, specific color, material** (if discernible), **pattern** (if any), and **fit/cut** (if applicable). List each description on a **new line, starting with a hyphen** (`-`). Example:
            `- a crisp white cotton crew-neck t-shirt, relaxed fit`
            `- a pair of dark blue slim-fit denim jeans`
            `- black leather ankle boots`
            `- a red and black plaid flannel shirt, oversized`
            """
            parts = [{"text": prompt}, {"image_uri": image_url}]
            response = self.vision_llm.invoke(parts)
            clothing_segment_str = response.content
            # Split by lines and clean up each part
            clothing_segments = [
                segment.strip().lstrip("- ").lower()
                for segment in clothing_segment_str.split("\n")
                if segment.strip()
            ]
            print(f"Segmented clothing parts for {image_url}: {clothing_segments}")
            return clothing_segments
        except Exception as e:
            print(f"Error segmenting clothing parts for {image_url}: {e}")
            return []

    def get_clothing_vibe(self, image_url: str) -> List[str]:
        """
        Determines the overall vibe or mood conveyed by the clothing in an image.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of terms describing the vibe (e.g., "relaxed", "sophisticated", "playful").
                       Returns an empty list if an error occurs.
        """
        try:
            # Optimized Prompt
            vibe_prompt = PromptTemplate(
                input_variables=["image_url"],
                template="""
                As a **fashion trend predictor**, determine the overall **'vibe' or 'mood'** conveyed by the clothing and styling of the person(s) in this image: `{image_url}`. Focus on emotions, feelings, and general impressions of the outfit. Examples: `relaxed, sophisticated, sporty, playful, elegant, edgy, formal, casual, energetic, cozy, bold, chic`. Provide **3-5 concise terms**, comma-separated. Example: `casual, comfortable, relaxed, approachable`
                """,
            )
            vibe_chain = LLMChain(llm=self.vision_llm, prompt=vibe_prompt)
            vibe_str = vibe_chain.run(image_url=image_url)
            vibe_terms = [t.strip().lower() for t in vibe_str.split(",") if t.strip()]
            print(f"Identified clothing vibe for {image_url}: {vibe_terms}")
            return vibe_terms
        except Exception as e:
            print(f"Error getting clothing vibe for {image_url}: {e}")
            return []

    def generate_tags(self, image_url: str) -> List[str]:
        """
        Generates descriptive tags for a clothing item using LLMChain for more structured output.

        Args:
            image_url (str): The URL of the image.

        Returns:
            List[str]: A list of generated tags.
                       Returns an empty list if an error occurs.
        """
        try:
            # Optimized Prompt
            tag_prompt = PromptTemplate(
                input_variables=["image_url"],
                template="""
                As an **expert tag generator for fashion items**, analyze the prominent clothing item or the main outfit in this image: `{image_url}`. Generate specific, relevant **tags** for the following categories, strictly adhering to the examples provided. **Only include categories that are clearly applicable.**
                - **Item Type**: e.g., `t-shirt, dress, jeans, jacket, skirt, sweater, shoes, hat`.
                - **Material**: e.g., `cotton, wool, silk, denim, leather, polyester, linen, cashmere`.
                - **Pattern**: e.g., `striped, floral, solid, plaid, polka dot, abstract, geometric, animal print`.
                - **Occasion**: e.g., `casual, formal, business, party, sport, lounge, streetwear`.
                - **Season**: e.g., `summer, winter, spring, autumn, all-season`.
                - **Fit/Cut**: e.g., `slim-fit, relaxed-fit, oversized, A-line, straight-leg, cropped, wide-leg`.
                - **Detailing**: e.g., `ripped, embroidered, sequined, plain, ruffled, zippered, button-down, hood`.
                - **Neckline**: e.g., `crew-neck, V-neck, scoop-neck, turtleneck`.
                - **Sleeve Length**: e.g., `short-sleeve, long-sleeve, sleeveless, 3/4 sleeve`.
                Return all applicable tags as a **single, comma-separated list**. Example: `t-shirt, cotton, solid, casual, summer, regular-fit, plain, crew-neck, short-sleeve`
                """,
            )
            tag_chain = LLMChain(llm=self.vision_llm, prompt=tag_prompt)
            tags_str = tag_chain.run(image_url=image_url)
            tags = [tag.strip().lower() for tag in tags_str.split(",") if tag.strip()]
            print(f"Generated tags for {image_url}: {tags}")
            return tags
        except Exception as e:
            print(f"Error generating tags for {image_url}: {e}")
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
            tag_results = db.session.query(Item.tags).distinct().all()
            all_tags = []
            for tags_tuple in tag_results:
                if tags_tuple[0] is not None:
                    all_tags.extend(tags_tuple[0])

            suggestions = [tag for tag in all_tags if query.lower() in tag.lower()]
            seen = set()
            suggestions = [
                tag for tag in suggestions if not (tag in seen or seen.add(tag))
            ]
            return suggestions[:limit]
        except Exception as e:
            print(f"Error getting tag suggestions: {e}")
            return []

    def recommend_outfit(
        self, user_id: str, season: str = "current", occasion: str = "casual"
    ) -> Dict[str, Any]:
        """
        Recommends a complete outfit based on a user's available items and specified season/occasion.

        Args:
            user_id (str): The ID of the user.
            season (str): The current season (e.g., "summer", "winter").
            occasion (str): The occasion for the outfit (e.g., "casual", "formal", "party").

        Returns:
            Dict[str, Any]: A dictionary containing the recommended outfit components.
                            Returns an empty dictionary if an error occurs or no items are found.
        """
        try:
            user_items = Item.query.filter_by(user_id=user_id).all()
            if not user_items:
                print(f"No items found for user {user_id}. Cannot recommend outfit.")
                return {}

            # Format user items for the prompt
            item_descriptions = [
                f"- {item.name}: {', '.join(item.tags or [])}" for item in user_items
            ]
            items_str = "\n".join(item_descriptions)

            # Optimized Prompt
            outfit_prompt = PromptTemplate(
                input_variables=["user_items", "season", "occasion"],
                template="""
                As your **personal fashion stylist**, I will recommend a complete and stylish outfit for the **{season} season** and a **{occasion} occasion**, using the following clothing items available to you:
                {user_items}
                Your recommendation **must** include:
                -   **Top**: (e.g., `White cotton t-shirt`)
                -   **Bottom**: (e.g., `Dark wash slim-fit jeans`)
                -   **Outerwear**: (if appropriate, e.g., `Light blue denim jacket` or `None`)
                -   **Footwear**: (e.g., `White canvas sneakers`)
                -   **Accessories**: (e.g., `Simple silver watch, black backpack` or `None`)
                Consider **color coordination, style matching, and seasonal appropriateness**. Be specific about item types and descriptions. Present the recommendation as a clear, structured list. Example:
                `- Top: White cotton t-shirt`
                `- Bottom: Dark wash slim-fit jeans`
                `- Outerwear: None`
                `- Footwear: White canvas sneakers`
                `- Accessories: Simple silver watch, black backpack`
                """,
            )

            outfit_chain = LLMChain(llm=self.text_llm, prompt=outfit_prompt)

            recommendation_text = outfit_chain.run(
                user_items=items_str,
                season=season,
                occasion=occasion,
            )

            # Parse the recommendation string into a structured dictionary
            recommended_outfit = {}
            for line in recommendation_text.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    parts = line[2:].split(": ", 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip()
                        recommended_outfit[key] = value

            print(
                f"Generated outfit recommendation for user {user_id}: {recommended_outfit}"
            )
            return recommended_outfit
        except Exception as e:
            print(f"Error generating outfit recommendation: {e}")
            return {}

    def get_recommendations(
        self, user_id: str, page: int = 1, per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Provides personalized item recommendations for a user with pagination.
        This can be expanded to use the AI's understanding of style, vibe, and
        other factors to suggest items.

        Args:
            user_id (str): The ID of the user.
            page (int): The page number for pagination.
            per_page (int): The number of items per page.

        Returns:
            Dict[str, Any]: A dictionary containing paginated results and metadata about the recommendations.
        """
        # TODO: Implement a more sophisticated personalized recommendation algorithm.
        # This currently returns public items as a placeholder.
        print(
            f"Getting placeholder recommendations for user {user_id}, page {page}, per_page {per_page}"
        )
        query = Item.query.filter(Item.is_public == True)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }

    def process_fashion_query_with_agent(
        self, query: str, image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Acts as a central agent to process complex fashion-related queries using available tools.
        This method showcases the agentic capability inspired by LangGraph.

        Args:
            query (str): The natural language query from the user (e.g., "What's the style and vibe of this outfit?").
            image_url (Optional[str]): The URL of the image to analyze, if the query requires image understanding.

        Returns:
            Dict[str, Any]: A dictionary containing the agent's findings and responses.
        """
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.messages import HumanMessage, SystemMessage

        # Prepare the tools with the current instance of AIService
        # LangChain's create_tool_calling_agent expects tools to be callable
        # directly or wrapped. Our _initialize_tools already provides this.
        tools_for_agent = self.tools

        # Define the agent's prompt
        # Optimized System Message for the Agent
        prompt = PromptTemplate.from_messages(
            [
                SystemMessage(
                    "You are a highly skilled and helpful **fashion AI assistant**. Your primary goal is to provide accurate and detailed insights into clothing and outfits. You can analyze images to understand styles, segment clothing parts, determine the overall vibe, generate relevant tags, and suggest outfit ideas. Utilize your available tools effectively to answer user queries comprehensively. If an image_url is provided in the query, prioritize image analysis tools."
                ),
                HumanMessage(content=query),
                # This will be filled by the agent's intermediate steps and tool calls
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create the agent
        agent = create_tool_calling_agent(self.agent_llm, tools_for_agent, prompt)

        # Create the AgentExecutor
        agent_executor = AgentExecutor(agent=agent, tools=tools_for_agent, verbose=True)

        try:
            # When calling the agent, provide image_url if applicable.
            # The agent's reasoning will then decide which tools need image_url.
            # The prompt needs to guide it to pick up the image_url if available.
            # For this simple setup, we'll pass it in the prompt explicitly if provided.
            if image_url:
                full_query = f"{query} (Image to analyze: {image_url})"
            else:
                full_query = query

            response = agent_executor.invoke({"input": full_query})
            return {"agent_response": response["output"]}

        except Exception as e:
            print(f"Error processing fashion query with agent: {e}")
            return {"error": str(e), "message": "Failed to process query."}


# Create a singleton instance of the AIService.
ai_service = AIService()
