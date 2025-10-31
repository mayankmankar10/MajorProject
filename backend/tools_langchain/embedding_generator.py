# backend/tools_langchain/embedding_generator.py
from langchain.tools import BaseTool
from langchain_openai import OpenAIEmbeddings
from typing import Type
from pydantic import BaseModel, Field
import os
import json
import logging

logger = logging.getLogger(__name__)

class EmbeddingGeneratorInput(BaseModel):
    """Input schema for EmbeddingGenerator."""
    text: str = Field(description="Text to generate embeddings for (job description, resume, etc.)")
    metadata_id: str = Field(default="", description="Optional ID to associate with this embedding")

class EmbeddingGenerator(BaseTool):
    """
    Generates vector embeddings for text using OpenAI's text-embedding-3-large model.
    """
    name: str = "EmbeddingGenerator"
    description: str = """
    Generates high-quality vector embeddings for text content.
    Used for semantic search, matching, and similarity calculations.
    
    Input:
    - text (string): The text to embed (job description, resume, profile, etc.)
    - metadata_id (string, optional): ID to track this embedding
    
    Output: JSON with embedding vector and metadata
    
    Use this when you need to create embeddings for semantic search or matching.
    """
    args_schema: Type[BaseModel] = EmbeddingGeneratorInput
    
    def __init__(self):
        super().__init__()
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _run(self, text: str, metadata_id: str = "") -> str:
        """Generate embeddings."""
        try:
            if not text or not text.strip():
                return json.dumps({"error": "Empty text provided", "embedding": []})
            
            # Generate embedding
            embedding_vector = self.embeddings.embed_query(text)
            
            result = {
                "embedding": embedding_vector,
                "dimension": len(embedding_vector),
                "metadata_id": metadata_id,
                "text_length": len(text),
                "success": True
            }
            
            logger.info(f"✅ Generated embedding (dim={len(embedding_vector)}) for text length={len(text)}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Embedding generation error: {str(e)}")
            return json.dumps({"error": str(e), "embedding": [], "success": False})
    
    async def _arun(self, text: str, metadata_id: str = "") -> str:
        """Async implementation."""
        return self._run(text, metadata_id)
