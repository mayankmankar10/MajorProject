# backend/tools_langchain/job_finder_tool.py
"""
Job search tool with TWO-WAY INTELLIGENT MATCHING.
Uses Gemini embeddings for semantic matching + personalized scoring.
"""
from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Job, Employee, Application, ProfileCache
from backend.db.vector_db import get_vector_store, get_embeddings
from backend.cache.tool_cache import tool_cache
import json
import logging
import re
import numpy as np

logger = logging.getLogger(__name__)


class JobFinderToolInput(BaseModel):
    """Input schema for JobFinderTool."""
    search_query: str = Field(description="Natural language job search query (e.g., 'chef jobs', 'cooking positions')")
    location: str = Field(default="", description="Optional location filter (e.g., 'Mumbai', 'Delhi')")
    job_type: str = Field(default="", description="Optional job type (full_time, part_time, contract)")
    limit: int = Field(default=10, description="Number of jobs to return")
    employee_id: int = Field(default=None, description="Employee ID for personalized two-way matching")


class JobFinderTool(BaseTool):
    """
    Searches for jobs using TWO-WAY INTELLIGENT MATCHING:
    1. Employee→Job: Does employee want this job? (preferences match)
    2. Job→Employee: Would employer select this employee? (qualifications)
    
    Final Score = Employee Preference (40%) + Employer Selection (60%)
    """
    name: str = "JobFinderTool"
    description: str = """
    Searches for jobs using AI-powered semantic search with TWO-WAY intelligent matching.
    
    Input:
    - search_query (string): Job search query (e.g., "cooking jobs", "server position")
    - location (string, optional): Location filter (e.g., "Mumbai")
    - job_type (string, optional): Job type filter (full_time, part_time)
    - limit (int, optional): Number of results (default 10)
    - employee_id (int, optional): Employee ID for personalized matching
    
    Output: JSON array of matching jobs ranked by TWO-WAY fit score
    
    The two-way matching considers:
    - Does employee WANT this job? (role, shift, salary, location preferences)
    - Would employer SELECT this employee? (experience, skills, qualifications)
    
    Use this when a candidate is searching for jobs.
    """
    args_schema: Type[BaseModel] = JobFinderToolInput
    
    def _parse_salary_range(self, salary_str: str) -> tuple:
        """Parse salary string to (min, max) integers."""
        if not salary_str:
            return (0, 999999)
        try:
            # Remove Rs., ₹, commas, spaces
            cleaned = re.sub(r'[Rs.₹,\s]', '', salary_str)
            parts = cleaned.split('-')
            if len(parts) == 2:
                return (int(parts[0].strip()), int(parts[1].strip()))
        except:
            pass
        return (0, 999999)
    
    def _calculate_employee_preference_score(self, employee: Employee, job: Job) -> dict:
        """
        Calculate how much the employee would WANT this job.
        Based on preferences (role, shift, salary, location, cuisine, job_type).
        Max score: 110 (Role:25, Shift:20, Salary:20, Location:20, Cuisine:15, JobType:10).
        Returns normalized to 0-100.
        """
        score = 0.0
        breakdown = {}
        
        # 1. Role match (+25 exact, +15 related)
        if employee.preferred_role and job.job_category:
            try:
                emp_role = employee.preferred_role.value
                job_role = job.job_category.value
                
                # Exact enum match
                if emp_role == job_role:
                    score += 25
                    breakdown["role_match"] = 25
                # Check if roles are related using comprehensive matching
                elif self._are_roles_related(emp_role, job_role):
                    score += 15
                    breakdown["role_related"] = 15
                # Fallback: check if role appears in job title
                elif emp_role.lower() in job.title.lower():
                    score += 10
                    breakdown["role_partial"] = 10
            except:
                pass
        
        # 2. Shift match (+20)
        if job.shift_type and employee.shift_preferences:
            if job.shift_type in employee.shift_preferences:
                score += 20
                breakdown["shift_match"] = 20
            elif employee.preferred_shift and job.shift_type == employee.preferred_shift:
                score += 20
                breakdown["shift_match"] = 20
        
        # 3. Salary fit (+20)
        if employee.expected_salary_min and employee.expected_salary_max and job.salary_range:
            job_min, job_max = self._parse_salary_range(job.salary_range)
            # Check if ranges overlap
            if employee.expected_salary_min <= job_max and employee.expected_salary_max >= job_min:
                score += 20
                breakdown["salary_fit"] = 20
        
        # 4. Location match (+20)
        if employee.preferred_location and job.location:
            emp_loc = employee.preferred_location.lower().strip()
            job_loc = job.location.lower().strip()
            if emp_loc in job_loc or job_loc in emp_loc:
                score += 20
                breakdown["location_match"] = 20
        
        # 5. Cuisine match (+15)
        if job.cuisine_type and employee.cuisine_experience:
            if job.cuisine_type in employee.cuisine_experience:
                score += 15
                breakdown["cuisine_match"] = 15
        
        # 6. Job type match (+10)
        if job.job_type and employee.preferred_job_type:
            if job.job_type in employee.preferred_job_type:
                score += 10
                breakdown["job_type_match"] = 10
        
        breakdown["total"] = score
        return {"score": min(score, 100), "breakdown": breakdown}
    
    def _calculate_profile_job_similarity(self, profile_text: str, job_text: str) -> float:
        """
        Calculate semantic similarity between employee profile and job description.
        Returns similarity score 0-100.
        """
        if not profile_text or not job_text:
            return 50.0  # Neutral score if missing data
        
        try:
            embeddings = get_embeddings()
            
            # Get embeddings for both texts
            profile_embedding = embeddings.embed_query(profile_text)
            job_embedding = embeddings.embed_query(job_text)
            
            # Calculate cosine similarity
            profile_vec = np.array(profile_embedding)
            job_vec = np.array(job_embedding)
            
            dot_product = np.dot(profile_vec, job_vec)
            norm_product = np.linalg.norm(profile_vec) * np.linalg.norm(job_vec)
            
            if norm_product == 0:
                return 50.0
            
            similarity = dot_product / norm_product  # Range: -1 to 1
            # Convert to 0-100 scale
            score = max(0, min(100, (similarity + 1) * 50))
            
            logger.debug(f"Profile-job similarity: {score:.1f}%")
            return score
            
        except Exception as e:
            logger.warning(f"Profile similarity calculation failed: {e}")
            return 50.0  # Fallback to neutral
    
    def _calculate_employer_selection_score(self, employee: Employee, job: Job, base_semantic: float) -> dict:
        """
        Calculate likelihood that employer would SELECT this employee.
        Uses PROFILE-BASED semantic matching (profile_summary vs enhanced_description).
        Returns score 0-100.
        """
        breakdown = {}
        
        # ENHANCED: Profile-based semantic match (40 points)
        # Match employee's profile_summary against job's enhanced_description
        profile_text = employee.profile_summary or ""
        job_text = job.enhanced_description or job.description or ""
        
        if profile_text and job_text:
            profile_similarity = self._calculate_profile_job_similarity(profile_text, job_text)
            score = min(profile_similarity * 0.4, 40)  # 40% weight
            breakdown["profile_match"] = round(score, 1)
            logger.debug(f"Profile→Job similarity: {profile_similarity:.1f}% → score: {score:.1f}")
        else:
            # Fallback to query-based semantic if no profile
            score = min(base_semantic * 0.4, 40)
            breakdown["semantic_base"] = round(score, 1)
        
        # 1. Experience fit (+15)
        min_exp = job.min_hospitality_experience or 0
        emp_exp = employee.years_in_hospitality or 0
        if emp_exp >= min_exp:
            score += 15
            breakdown["experience_fit"] = 15
        elif emp_exp >= min_exp - 1:  # Allow 1 year gap
            score += 8
            breakdown["experience_partial"] = 8
        
        # 2. Certification bonus (+15)
        cert_score = 0
        if job.requires_food_safety and employee.food_safety_certified:
            cert_score += 7.5
        if job.requires_alcohol_cert and employee.alcohol_service_certified:
            cert_score += 7.5
        if cert_score > 0:
            score += cert_score
            breakdown["certifications"] = round(cert_score, 1)
        
        # 3. Cuisine experience match (+15)
        if job.cuisine_type and employee.cuisine_experience:
            if job.cuisine_type in employee.cuisine_experience:
                score += 15
                breakdown["cuisine_exp"] = 15
        
        # 4. Skills match (check profile cache for top skills) (+10)
        # This would need ProfileCache but we'll use a simpler check
        if employee.skills and job.description:
            job_desc_lower = job.description.lower()
            matched_skills = sum(1 for skill in employee.skills if skill.lower() in job_desc_lower)
            if matched_skills >= 2:
                score += 10
                breakdown["skills_match"] = 10
            elif matched_skills == 1:
                score += 5
                breakdown["skills_partial"] = 5
        
        # 5. Shift availability (+5)
        if job.shift_type and employee.shift_preferences:
            if job.shift_type in employee.shift_preferences:
                score += 5
                breakdown["shift_available"] = 5
        
        return {"score": min(score, 100), "breakdown": breakdown}
    
    def _are_roles_related(self, role1: str, role2: str) -> bool:
        """
        Check if two hospitality roles are related/similar.
        Reused from MatchingTool for consistency.
        
        Examples:
            - cook ~ chef = True
            - bartender ~ sommelier = True  
            - server ~ waiter = True
            - chef ~ bartender = False
        """
        role1 = role1.lower().strip()
        role2 = role2.lower().strip()
        
        # Same role
        if role1 == role2 or role1 in role2 or role2 in role1:
            return True
        
        # Related role groups (comprehensive hospitality roles)
        related_groups = [
            # Kitchen roles
            {"chef", "cook", "line cook", "sous chef", "head chef", "senior chef", 
             "pastry chef", "executive chef", "kitchen staff", "prep cook", "commis chef"},
            # Bar roles
            {"bartender", "mixologist", "barista", "bar manager", "head bartender", 
             "sommelier", "beverage manager", "beverage", "bar", "bar staff"},
            # Service roles  
            {"server", "waiter", "waitress", "waitstaff", "food runner", "service staff"},
            # Host roles
            {"host", "hostess", "greeter", "receptionist", "front desk"},
            # Management roles
            {"manager", "supervisor", "team lead", "shift lead", "restaurant manager",
             "floor manager", "operations manager", "general manager"},
            # Kitchen helper roles
            {"dishwasher", "kitchen helper", "kitchen porter", "busser", "utility"},
        ]
        
        for group in related_groups:
            role1_in_group = any(r in role1 or role1 in r for r in group)
            role2_in_group = any(r in role2 or role2 in r for r in group)
            if role1_in_group and role2_in_group:
                return True
        
        return False
    
    def _should_exclude_job(self, employee: Employee, job: Job, applied_job_ids: set) -> str:
        """
        Check if job should be excluded entirely.
        Returns reason string if excluded, None if OK.
        
        NOTE: We only filter by role and already-applied.
        Salary/experience matching is handled by the TWO-WAY SCORING system,
        which naturally ranks appropriate jobs higher.
        """
        # 1. Already applied
        if job.id in applied_job_ids:
            return "already_applied"
            
        # 2. Salary filter (Reinstated 1.5x limit)
        if employee.expected_salary_max and job.salary_range:
            job_min, _ = self._parse_salary_range(job.salary_range)
            if job_min > employee.expected_salary_max * 1.5:
                return "salary_too_high"
        
        # 3. Role relevance filter - exclude completely unrelated roles
        if employee.preferred_role and job.job_category:
            try:
                emp_role = employee.preferred_role.value.lower()
                job_role = job.job_category.value.lower()
                
                # Check exact match
                if emp_role == job_role:
                    return None  # Perfect match, don't exclude
                
                # Check if roles are related using comprehensive matching
                if self._are_roles_related(emp_role, job_role):
                    return None  # Related roles, don't exclude
                
                # Only exclude if roles are completely unrelated
                return "role_mismatch"
            except:
                pass
        
        return None
    
    def _run(
        self,
        search_query: str,
        location: str = "",
        job_type: str = "",
        limit: int = 10,
        employee_id: int = None
    ) -> str:
        """Search for jobs using two-way intelligent matching."""
        
        try:
            db: Session = next(get_db())
            results = []
            search_method = "semantic"
            employee = None
            applied_job_ids = set()
            
            # Load employee profile if provided
            if employee_id:
                employee = db.query(Employee).filter(Employee.id == employee_id).first()
                if employee:
                    # Get already-applied job IDs
                    applications = db.query(Application).filter(
                        Application.employee_id == employee_id
                    ).all()
                    applied_job_ids = {app.job_id for app in applications}
                    
                    # Use employee's preferred location if not specified
                    if not location and employee.preferred_location:
                        location = employee.preferred_location
                    
                    logger.info(f"🎯 Two-way matching for employee {employee_id} ({employee.full_name})")
            
            # Check cache (only for non-personalized searches)
            if not employee_id:
                cached = tool_cache.get(
                    "JobFinderTool",
                    query=search_query,
                    location=location,
                    job_type=job_type,
                    limit=limit
                )
                if cached:
                    logger.info(f"✅ Cache HIT for job search: '{search_query}'")
                    return cached
            
            # Try semantic search first using job embeddings
            job_store = get_vector_store("job")
            
            if job_store and search_query:
                logger.info(f"🔍 Using SEMANTIC search for: '{search_query}'")
                
                # Get more results than needed for post-filtering
                semantic_results = job_store.similarity_search_with_score(
                    search_query,
                    k=min(limit * 5, 100)  # Get extra for intelligent filtering
                )
                
                for doc, distance in semantic_results:
                    job_id = doc.metadata.get("id")
                    job_location = doc.metadata.get("location", "")
                    job_job_type = doc.metadata.get("job_type", "")
                    
                    # Apply location filter if specified
                    if location and job_location:
                        if location.lower() not in job_location.lower():
                            continue
                    
                    # Apply job_type filter if specified
                    if job_type and job_job_type:
                        if job_type.lower() != job_job_type.lower():
                            continue
                    
                    # Calculate base semantic score (0-100)
                    base_semantic = max(0, 100 * (1 - distance / 2))
                    
                    # TWO-WAY INTELLIGENT MATCHING
                    if employee:
                        # Fetch full job object for detailed scoring
                        job = db.query(Job).filter(Job.id == job_id).first()
                        if not job:
                            continue
                        
                        # Check exclusion filters
                        exclusion_reason = self._should_exclude_job(employee, job, applied_job_ids)
                        if exclusion_reason:
                            logger.debug(f"Excluding job {job_id}: {exclusion_reason}")
                            continue
                        
                        # Calculate two-way scores
                        emp_pref = self._calculate_employee_preference_score(employee, job)
                        emp_select = self._calculate_employer_selection_score(employee, job, base_semantic)
                        
                        # Combined score: Employee Preference (40%) + Employer Selection (60%)
                        final_score = (emp_pref["score"] * 0.4) + (emp_select["score"] * 0.6)
                        
                        results.append({
                            "job_id": job_id,
                            "title": doc.metadata.get("title", "Unknown"),
                            "company": doc.metadata.get("company_name", "Unknown"),
                            "location": job_location,
                            "job_type": job_job_type,
                            "salary_range": doc.metadata.get("salary_range"),
                            "description": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "match_score": round(final_score, 2),
                            "preference_score": round(emp_pref["score"], 2),
                            "selection_score": round(emp_select["score"], 2),
                            "score_breakdown": {
                                "employee_wants": emp_pref["breakdown"],
                                "employer_likely": emp_select["breakdown"]
                            }
                        })
                    else:
                        # Simple semantic scoring (no employee profile)
                        results.append({
                            "job_id": job_id,
                            "title": doc.metadata.get("title", "Unknown"),
                            "company": doc.metadata.get("company_name", "Unknown"),
                            "location": job_location,
                            "job_type": job_job_type,
                            "salary_range": doc.metadata.get("salary_range"),
                            "description": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "relevance_score": round(base_semantic, 2)
                        })
                    
                    if len(results) >= limit * 2:  # Get extra for deduplication
                        break
                
                # Deduplicate: keep only one job per (title, company) combination
                seen_jobs = {}
                score_key = "match_score" if employee else "relevance_score"
                for job in results:
                    key = (job["title"].lower().strip(), job["company"].lower().strip())
                    if key not in seen_jobs:
                        seen_jobs[key] = job
                    elif job.get(score_key, 0) > seen_jobs[key].get(score_key, 0):
                        seen_jobs[key] = job
                
                # Sort by score and take top results
                results = sorted(seen_jobs.values(), key=lambda x: -x.get(score_key, 0))[:limit]
                
                logger.info(f"✅ {'Two-way' if employee else 'Semantic'} search found {len(results)} unique jobs")
            
            # Fallback to SQL if no job store or no results
            if not results:
                logger.info(f"📊 Falling back to SQL search for: '{search_query}'")
                search_method = "sql_fallback"
                
                query = db.query(Job).filter(Job.is_active == True)
                
                if location:
                    query = query.filter(Job.location.ilike(f"%{location}%"))
                
                if job_type:
                    query = query.filter(Job.job_type == job_type)
                
                if search_query:
                    search_filter = (
                        Job.title.ilike(f"%{search_query}%") |
                        Job.description.ilike(f"%{search_query}%")
                    )
                    query = query.filter(search_filter)
                
                jobs = query.order_by(Job.created_at.desc()).limit(limit * 2).all()
                
                for job in jobs:
                    # Apply exclusion filters for employee
                    if employee:
                        exclusion_reason = self._should_exclude_job(employee, job, applied_job_ids)
                        if exclusion_reason:
                            continue
                    
                    results.append({
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.employer.company_name if job.employer else "Unknown",
                        "location": job.location,
                        "job_type": job.job_type,
                        "salary_range": job.salary_range,
                        "description": job.description[:200] + "..." if job.description and len(job.description) > 200 else (job.description or ""),
                        "relevance_score": None
                    })
                
                results = results[:limit]
                logger.info(f"✅ SQL fallback found {len(results)} jobs")
            
            result = {
                "jobs": results,
                "total": len(results),
                "query": search_query,
                "search_method": search_method if not employee else "two_way_intelligent",
                "personalized": employee_id is not None,
                "success": True
            }
            
            if not results:
                result["message"] = "No matching jobs found. Try broadening your search."
            
            result_json = json.dumps(result)
            
            # Cache only non-personalized results
            if not employee_id:
                tool_cache.set(
                    "JobFinderTool",
                    result_json,
                    ttl=900,
                    query=search_query,
                    location=location,
                    job_type=job_type,
                    limit=limit
                )
            
            # Save results to session context for "Apply to #1" functionality
            from backend.context import set_session_data
            
            # Store just the essentials: list of {job_id, match_score}
            # This allows JobApplicationTool to lookup by index
            job_context = [
                {"job_id": j["job_id"], "match_score": j.get("match_score", 0)} 
                for j in results
            ]
            set_session_data("last_job_search_results", job_context)
            logger.info(f"💾 Saved {len(job_context)} jobs to session context")

            logger.info(f"✅ JobFinderTool: {len(results)} jobs via {result['search_method']}")
            return result_json
            
        except Exception as e:
            logger.error(f"❌ Job search error: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e), "jobs": [], "success": False})
    
    async def _arun(
        self,
        search_query: str,
        location: str = "",
        job_type: str = "",
        limit: int = 10,
        employee_id: int = None
    ) -> str:
        """Async implementation."""
        return self._run(search_query, location, job_type, limit, employee_id)
