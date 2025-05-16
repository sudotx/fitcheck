import os
from typing import List, Tuple

import google.generativeai as genai
from langchain.chains import LLMChain
from langchain.embeddings import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Config


class AIService:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=Config.goo)
        self.model = genai.GenerativeModel("gemini-pro-vision")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", google_api_key=Config.GOOGLE_API_KEY
        )
        self.vector_store = FAISS.from_texts(
            ["initial"], self.embeddings
        )  # Initialize with dummy text

        # Initialize LLM for text generation
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.7,
        )

    def generate_embedding(self, image) -> List[float]:
        """Generate embedding for an image using Gemini Vision"""
        response = self.model.generate_content(
            [
                "Generate a detailed description of this clothing item, including style, color, and type.",
                image,
            ]
        )
        description = response.text

        # Generate embedding from the description
        embedding = self.embeddings.embed_query(description)
        return embedding

    def add_to_index(self, embedding: List[float], item_id: str):
        """Add an embedding to the FAISS index"""
        self.vector_store.add_embeddings(text_embeddings=[(str(item_id), embedding)])

    def search_similar(
        self, embedding: List[float], k: int = 5
    ) -> List[Tuple[str, float]]:
        """Search for similar items using FAISS"""
        results = self.vector_store.similarity_search_with_score_by_vector(
            embedding, k=k
        )
        return [(doc.metadata.get("item_id"), score) for doc, score in results]

    def generate_tags(self, image) -> List[str]:
        """Generate style tags for an image using Gemini Vision"""
        prompt = PromptTemplate(
            input_variables=["image"],
            template="""
            Analyze this clothing item and provide exactly 3 style tags that best describe it.
            Choose from these categories: casual, formal, vintage, streetwear, sporty, bohemian, 
            minimalist, grunge, preppy, elegant.
            Return only the tags, separated by commas.
            """,
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(image=image)

        # Parse the response to get tags
        tags = [tag.strip() for tag in response.split(",")]
        return tags[:3]  # Ensure we only return 3 tags

    def analyze_outfit(self, images: List) -> str:
        """Analyze a complete outfit using Gemini Vision"""
        prompt = PromptTemplate(
            input_variables=["images"],
            template="""
            Analyze this outfit combination and provide:
            1. Overall style assessment
            2. Color coordination
            3. Occasion appropriateness
            4. Suggestions for improvement
            """,
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(images=images)


ai_service = AIService()
