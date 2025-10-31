# backend/tools_langchain/matching_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from backend.db.vector_db import get_vector_store
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Employee, Job
import json
import logging

logger = logging.getLogger(__name__)

class MatchingToolInput(BaseModel):
    """Input schema for MatchingTool."""
    query_text: str = Field(description="Text to match against (job description or resume)")
    match_type: str = Field(description="Type of match: 'job_to_candidates' or 'candidate_to_jobs'")
    top_k: int = Field(default=5, description="Number of top matches to return")

class MatchingTool(BaseTool):
    """
    Performs semantic similarity matching using ChromaDB vector search.
    Finds best candidates for jobs or best jobs for candidates.
    """
    name: str = "MatchingTool"
    description: str = """
    Performs semantic matching between jobs and candidates using vector similarity.
    
    Input:
    - query_text (string): Job description or resume text to match
    - match_type (string): Either 'job_to_candidates' or 'candidate_to_jobs'
    - top_k (int, optional): Number of matches to return (default 5)
    
    Output: JSON array of matches with IDs, scores, and snippets
    
    Use this to find the best candidates for a job or the best jobs for a candidate.
    """
    args_schema: Type[BaseModel] = MatchingToolInput
    
    def _run(self, query_text: str, match_type: str, top_k: int = 5) -> str:
        """Perform semantic matching."""
        try:
            vector_store = get_vector_store()
            db: Session = next(get_db())
            
            # Determine collection based on match type
            if match_type == "job_to_candidates":
                collection_name = "employee_profiles"
            elif match_type == "candidate_to_jobs":
                collection_name = "job_postings"
            else:
                return json.dumps({"error": "Invalid match_type. Use 'job_to_candidates' or 'candidate_to_jobs'"})
            
            # Perform vector search
            collection = vector_store.get_collection(name=collection_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=min(top_k, 10)
            )
            
            matches = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    match = {
                        "id": doc_id,
                        "score": float(1 - results['distances'][0][i]) if results['distances'] else 0.0,
                        "snippet": results['documents'][0][i][:200] if results['documents'] else "",
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    }
                    matches.append(match)
            
            result = {
                "matches": matches,
                "total": len(matches),
                "match_type": match_type,
                "success": True
            }
            
            logger.info(f"✅ Found {len(matches)} matches for {match_type}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Matching error: {str(e)}")
            return json.dumps({"error": str(e), "matches": [], "success": False})
    
    async def _arun(self, query_text: str, match_type: str, top_k: int = 5) -> str:
        """Async implementation."""
        return self._run(query_text, match_type, top_k)
