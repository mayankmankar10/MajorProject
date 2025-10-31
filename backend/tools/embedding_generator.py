# backend/tools/embedding_generator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import List
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class EmbeddingInput(BaseModel):
    """Input schema for EmbeddingGenerator."""
    text: str = Field(description="Text to generate embedding for")


class EmbeddingGenerator(BaseTool):
    """Tool for generating text embeddings using OpenAI's embedding model."""
    
    name: str = "generate_embedding"
    description: str = """
    Generate a vector embedding from text using OpenAI's text-embedding-3-large model.
    Use this for:
    - Creating job description embeddings for semantic search
    - Creating resume embeddings for candidate matching
    - Vectorizing any text for similarity comparison
    
    Returns a 3072-dimensional embedding vector.
    """
    args_schema: type[BaseModel] = EmbeddingInput
    
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    
    def _run(self, text: str) -> dict:
        """Generate embedding for text."""
        try:
            if not text or not text.strip():
                return {
                    "status": "error",
                    "message": "Empty text provided"
                }
            
            # Generate embedding
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            logger.info(f"Generated embedding for text (length: {len(text)} chars)")
            
            return {
                "status": "success",
                "embedding": embedding,
                "dimensions": len(embedding),
                "model": self.model,
                "text_length": len(text)
            }
        
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate embedding: {str(e)}"
            }
    
    async def _arun(self, text: str) -> dict:
        """Async version - calls sync implementation."""
        return self._run(text)


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Helper function to generate embeddings for multiple texts at once."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        
        return [item.embedding for item in response.data]
    
    except Exception as e:
        logger.error(f"Batch embedding error: {e}")
        return []
