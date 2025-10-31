# backend/tools/matching_tool.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import List, Literal
import logging
from backend.db.vector_db import get_vector_store
from backend.db.sql_db import SessionLocal
from backend.db.models import Job, Employee

logger = logging.getLogger(__name__)


class MatchingInput(BaseModel):
    """Input schema for MatchingTool."""
    query_text: str = Field(description="Text to match against (job description or resume)")
    match_type: Literal["jobs", "candidates"] = Field(description="Type: 'jobs' to find jobs, 'candidates' to find candidates")
    top_k: int = Field(default=10, description="Number of top matches to return")


class MatchingTool(BaseTool):
    """Tool for semantic matching between jobs and candidates using vector similarity."""
    
    name: str = "semantic_match"
    description: str = """
    Find the best semantic matches between jobs and candidates using vector similarity search.
    
    Use this tool to:
    - Find top matching candidates for a job posting (match_type='candidates')
    - Find top matching jobs for an employee's profile (match_type='jobs')
    
    The tool uses ChromaDB with OpenAI embeddings for semantic search.
    Returns match scores (0-1, higher is better) with entity details.
    """
    args_schema: type[BaseModel] = MatchingInput
    
    def _run(
        self,
        query_text: str,
        match_type: Literal["jobs", "candidates"],
        top_k: int = 10
    ) -> dict:
        """Perform semantic matching."""
        try:
            # Get vector store
            vector_store = get_vector_store()
            
            # Determine collection and metadata filter
            if match_type == "jobs":
                collection_name = "job_embeddings"
                doc_type_filter = "job"
            else:  # candidates
                collection_name = "resume_embeddings"
                doc_type_filter = "resume"
            
            # Perform similarity search with scores
            try:
                results = vector_store.similarity_search_with_score(
                    query=query_text,
                    k=top_k,
                    filter={"document_type": doc_type_filter}
                )
            except:
                # Fallback without filter if collection doesn't support it
                results = vector_store.similarity_search_with_score(
                    query=query_text,
                    k=top_k
                )
            
            # Process results
            matches = []
            db = SessionLocal()
            try:
                for doc, score in results:
                    metadata = doc.metadata
                    
                    # Get additional details from database
                    if match_type == "jobs":
                        job_id = metadata.get("job_id")
                        if job_id:
                            job = db.query(Job).filter(Job.id == job_id).first()
                            if job:
                                matches.append({
                                    "id": job.id,
                                    "title": job.title,
                                    "location": job.location,
                                    "company": job.employer.company_name if job.employer else None,
                                    "match_score": float(1 - score),  # Convert distance to similarity
                                    "snippet": doc.page_content[:200]
                                })
                    else:  # candidates
                        employee_id = metadata.get("employee_id")
                        if employee_id:
                            employee = db.query(Employee).filter(Employee.id == employee_id).first()
                            if employee:
                                matches.append({
                                    "id": employee.id,
                                    "name": employee.full_name,
                                    "skills": employee.skills or [],
                                    "experience_years": employee.experience_years,
                                    "match_score": float(1 - score),
                                    "snippet": doc.page_content[:200]
                                })
            finally:
                db.close()
            
            # Sort by match score descending
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            
            logger.info(f"Found {len(matches)} {match_type} matches")
            
            return {
                "status": "success",
                "match_type": match_type,
                "matches": matches,
                "total_found": len(matches)
            }
        
        except Exception as e:
            logger.error(f"Matching error: {e}")
            return {
                "status": "error",
                "message": f"Failed to perform matching: {str(e)}",
                "matches": []
            }
    
    async def _arun(self, *args, **kwargs) -> dict:
        """Async version - calls sync implementation."""
        return self._run(*args, **kwargs)
