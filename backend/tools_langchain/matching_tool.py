# backend/tools_langchain/matching_tool.py
from langchain.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.db.vector_db import get_vector_store, DEFAULT_MATCH_THRESHOLD, CANDIDATE_JOB_THRESHOLD
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Employee, Job, ProfileCache
from backend.cache.tool_cache import tool_cache
import json
import logging

logger = logging.getLogger(__name__)

class MatchingToolInput(BaseModel):
    """Input schema for MatchingTool."""
    query_text: str = Field(description="Text to match against (job description or resume)")
    match_type: str = Field(description="Type of match: 'job_to_candidates' or 'candidate_to_jobs'")
    top_k: int = Field(default=5, description="Number of top matches to return")
    job_id: int = Field(default=None, description="Optional job_id for restaurant-specific scoring")
    role: str = Field(default=None, description="Optional role (e.g., 'bartender') for role-based bonus scoring in direct hiring")

class MatchingTool(BaseTool):
    """
    Performs semantic similarity matching using ChromaDB vector search.
    Enhanced with restaurant-specific scoring for cafe/restaurant hiring.
    """
    name: str = "MatchingTool"
    description: str = """
    Performs semantic matching between jobs and candidates.
    ENHANCED with restaurant-specific scoring (certifications, cuisine, shifts).
    
    IMPORTANT: This tool is primarily for EMPLOYERS to find candidates for their jobs.
    For EMPLOYEES searching for jobs, use JobFinderTool instead (it's faster and more accurate).
    
    Input:
    - query_text (string): Job description or resume text to match
    - match_type (string): 'job_to_candidates' (find employees for a job) or 'candidate_to_jobs' (find jobs for employee)
    - top_k (int, optional): Number of matches to return (default 5)
    - job_id (int, optional): Job ID for restaurant-specific scoring bonuses
    
    Output: JSON array of matches with IDs, enhanced scores, and snippets
    
    Restaurant scoring bonuses (for job_to_candidates):
    - Certifications match: +10 points
    - Cuisine experience: +15 points
    - Shift availability: +5 points
    - Experience level: +10 points
    - Customer service (for front-of-house): +10 points
    """
    args_schema: Type[BaseModel] = MatchingToolInput

    llm: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _get_role_cert_requirements(self, role: str) -> dict:
        """Get certification requirements based on hospitality role."""
        if not role:
            return {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": False}
        
        role_lower = role.lower().strip()
        role_requirements = {
            # Front-of-house (customer-facing)
            "bartender": {"needs_alcohol": True, "needs_food_safety": True, "is_front_of_house": True},
            "server": {"needs_alcohol": True, "needs_food_safety": True, "is_front_of_house": True},
            "waiter": {"needs_alcohol": True, "needs_food_safety": True, "is_front_of_house": True},
            "host": {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": True},
            "hostess": {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": True},
            # Back-of-house (kitchen)
            "cook": {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": False},
            "chef": {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": False},
            "dishwasher": {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": False},
            # Management
            "manager": {"needs_alcohol": True, "needs_food_safety": True, "is_front_of_house": True}
        }
        return role_requirements.get(role_lower, {"needs_alcohol": False, "needs_food_safety": True, "is_front_of_house": False})
    
    def _are_roles_related(self, role1: str, role2: str) -> bool:
        """
        Check if two hospitality roles are related/similar.
        Used for partial role matching bonus.
        
        Examples:
            - cook ~ chef = True
            - bartender ~ mixologist = True  
            - server ~ waiter = True
            - chef ~ bartender = False
        """
        role1 = role1.lower().strip()
        role2 = role2.lower().strip()
        
        # Same role
        if role1 == role2 or role1 in role2 or role2 in role1:
            return True
        
        # Related role groups
        related_groups = [
            # Kitchen roles
            {"chef", "cook", "line cook", "sous chef", "head chef", "senior chef", "pastry chef", "executive chef"},
            # Bar roles
            {"bartender", "mixologist", "barista", "bar manager", "head bartender", "sommelier", "beverage"},
            # Service roles
            {"server", "waiter", "waitress", "waitstaff", "food runner"},
            # Host roles
            {"host", "hostess", "greeter", "receptionist"},
            # Management roles
            {"manager", "supervisor", "team lead", "shift lead", "restaurant manager"},
            # Kitchen helper roles
            {"dishwasher", "kitchen helper", "kitchen porter", "busser"},
        ]
        
        for group in related_groups:
            role1_in_group = any(r in role1 or role1 in r for r in group)
            role2_in_group = any(r in role2 or role2 in r for r in group)
            if role1_in_group and role2_in_group:
                return True
        
        return False
    
    def _calculate_restaurant_bonus(self, employee: Employee, job: Job = None, cached_profile: ProfileCache = None, requirements: dict = None) -> float:
        """
        Calculate restaurant-specific bonus score.
        Returns bonus points (0-50) based on restaurant criteria.
        
        Args:
            employee: Employee object
            job: Job object (optional, for job-based matching)
            cached_profile: ProfileCache object (optional)
            requirements: Dict with shift_requirements, etc. (optional, for direct hiring)
        """
        bonus = 0.0
        
        # Get requirements from either job object or requirements dict
        shift_requirements = requirements.get('shift_requirements', []) if requirements else None
        min_experience = requirements.get('min_experience') if requirements else None
        
        # Bonus 1: Certification match (+15 points max)
        if job:
            # Job-based: use actual job requirements
            if job.requires_food_safety and employee.food_safety_certified:
                bonus += 10
                logger.debug(f"  +10 (food safety cert)")
            
            if job.requires_alcohol_cert and employee.alcohol_service_certified:
                bonus += 5
                logger.debug(f"  +5 (alcohol cert)")
        elif requirements and 'role' in requirements:
            # Direct hiring: use role-based certification requirements
            role_certs = self._get_role_cert_requirements(requirements['role'])
            
            if role_certs.get('needs_food_safety') and employee.food_safety_certified:
                bonus += 10
                logger.info(f"  +10 (food safety - role-based: {requirements['role']})")
            
            if role_certs.get('needs_alcohol') and employee.alcohol_service_certified:
                bonus += 5
                logger.info(f"  +5 (alcohol cert - role-based: {requirements['role']})")
        
        # Bonus 2: Cuisine experience match (+15 points)
        if job and job.cuisine_type and employee.cuisine_experience:
            if job.cuisine_type in employee.cuisine_experience:
                bonus += 15
                logger.debug(f"  +15 (cuisine: {job.cuisine_type})")
        
        # Bonus 3: Shift availability match (+5 points)
        # Check job.shift_type OR requirements.shift_requirements
        matched_shift = False
        if job and job.shift_type and employee.shift_preferences:
            if job.shift_type in employee.shift_preferences:
                bonus += 5
                matched_shift = True
                logger.debug(f"  +5 (shift: {job.shift_type})")
        elif shift_requirements and employee.shift_preferences:
            # For direct hiring: check if employee has ANY of the required shifts
            if any(shift in employee.shift_preferences for shift in shift_requirements):
                bonus += 5
                matched_shift = True
                logger.debug(f"  +5 (shift match: {shift_requirements})")
        
        # Bonus 4: Experience level match (+10 points)
        if job:
            min_exp = job.min_hospitality_experience or 0
            if employee.years_in_hospitality >= min_exp:
                bonus += 10
                logger.debug(f"  +10 (experience: {employee.years_in_hospitality} >= {min_exp})")
        elif min_experience and employee.years_in_hospitality >= min_experience:
            bonus += 10
            logger.debug(f"  +10 (experience: {employee.years_in_hospitality} >= {min_experience})")
        
        # Bonus 5: Customer service for front-of-house roles (+10 points)
        if job and job.job_category and job.job_category.value in ["waiter", "host", "bartender"]:
            # Check if employee has "customer service" in their skills
            if employee.skills:
                customer_service_keywords = ["customer service", "hospitality", "guest relations", "service"]
                if any(keyword in str(employee.skills).lower() for keyword in customer_service_keywords):
                    bonus += 10
                    logger.debug(f"  +10 (customer service skills)")
        elif requirements and 'role' in requirements:
            role_certs = self._get_role_cert_requirements(requirements['role'])
            if role_certs.get('is_front_of_house') and employee.skills:
                customer_service_keywords = ["customer service", "hospitality", "guest relations"]
                if any(keyword in str(employee.skills).lower() for keyword in customer_service_keywords):
                    bonus += 10
                    logger.debug(f"  +10 (customer service - role-based)")
        
        # Bonus 6: Job type match (+5 points)
        if job and job.job_type and employee.preferred_job_type:
            if job.job_type in employee.preferred_job_type:
                bonus += 5
                logger.debug(f"  +5 (job type: {job.job_type})")
        
        return min(bonus, 50)  # Cap at 50 bonus points
    
    async def _arun(self, query_text: str, match_type: str, top_k: int = 5, job_id: int = None, shift_requirements: list = None, role: str = None) -> str:
        """Async version - delegates to sync _run."""
        return self._run(query_text, match_type, top_k, job_id, shift_requirements, role)
    def _run(self, query_text: str, match_type: str, top_k: int = 5, job_id: int = None, shift_requirements: list = None, role: str = None) -> str:
        """Perform semantic matching with restaurant-specific enhancements."""
        # Check cache first
        cached = tool_cache.get(
            "MatchingTool",
            query=query_text,
            match_type=match_type,
            top_k=top_k,
            job_id=job_id,
            shift_requirements=shift_requirements
        )
        if cached:
            logger.info(f"âœ… Cache HIT for matching: {match_type}")
            return cached
        
        try:
            db = SessionLocal()
            
            try:
                # For candidate_to_jobs: Use HYBRID search (semantic + keyword)
                if match_type == "candidate_to_jobs":
                    logger.info(f"ðŸ” Performing HYBRID job search (semantic + keyword)...")
                    
                    # Get job vector store
                    job_store = get_vector_store("job")
                    
                    matches = []
                    
                    if job_store:
                        # Use semantic search via job embeddings
                        logger.info("Using semantic search via Gemini job embeddings")
                        results = job_store.similarity_search_with_score(
                            query_text,
                            k=min(top_k * 2, 20)
                        )
                        
                        for doc, distance in results:
                            job_id_match = doc.metadata.get("id")
                            
                            # Semantic score (FAISS returns L2 distance, convert to similarity)
                            # Lower distance = better match, typical range 0-2
                            # Scale to 0-60 base score (leaving room for bonuses)
                            semantic_score = max(0, 60 * (1 - distance / 2))
                            
                            # Also calculate keyword overlap bonus (up to 15 points)
                            job_text = doc.page_content.lower()
                            query_words = set(query_text.lower().split())
                            doc_words = set(job_text.split())
                            keyword_overlap = len(query_words & doc_words)
                            keyword_bonus = min(keyword_overlap * 3, 15)
                            
                            # ROLE MATCH - Critical for ranking jobs by preferred role
                            # Use as a MULTIPLIER to ensure role-matched jobs always rank higher
                            role_multiplier = 1.0
                            role_bonus = 0
                            job_title = doc.metadata.get("title", "").lower()
                            job_category = doc.metadata.get("job_category", "").lower() if doc.metadata.get("job_category") else ""
                            
                            # Extract role from query (format: "Role: CHEF" or similar)
                            preferred_role = ""
                            if "role:" in query_text.lower():
                                role_start = query_text.lower().find("role:") + 5
                                role_end = query_text.find(".", role_start)
                                if role_end == -1:
                                    role_end = len(query_text)
                                preferred_role = query_text[role_start:role_end].strip().lower()
                            
                            if preferred_role:
                                # Exact role match: 1.4x multiplier + 25 bonus points
                                if preferred_role in job_title or preferred_role in job_category:
                                    role_multiplier = 1.4
                                    role_bonus = 25
                                    logger.debug(f"  x1.4 +25 (exact role match: {preferred_role} in {job_title})")
                                # Related roles: 1.2x multiplier + 15 bonus points
                                elif self._are_roles_related(preferred_role, job_title) or self._are_roles_related(preferred_role, job_category):
                                    role_multiplier = 1.2
                                    role_bonus = 15
                                    logger.debug(f"  x1.2 +15 (related role match: {preferred_role} ~ {job_title})")
                                # Non-matching role: 0.7x penalty
                                else:
                                    role_multiplier = 0.7
                                    logger.debug(f"  x0.7 (role mismatch: {preferred_role} != {job_title})")
                            
                            # Calculate final score: base * multiplier + bonuses
                            # Don't cap at 100 - allow higher scores for better ranking
                            base_score = semantic_score + keyword_bonus
                            final_score = (base_score * role_multiplier) + role_bonus
                            # Now cap at 100 for display purposes
                            display_score = min(final_score, 100)
                            
                            match = {
                                "id": job_id_match,
                                "job_id": job_id_match,
                                "title": doc.metadata.get("title", "Unknown"),
                                "company_name": doc.metadata.get("company_name", "Unknown"),
                                "location": doc.metadata.get("location"),
                                "job_type": doc.metadata.get("job_type"),
                                "salary_range": doc.metadata.get("salary_range"),
                                "base_score": round(float(semantic_score), 2),
                                "bonus_score": round(float(keyword_bonus + role_bonus), 2),
                                "final_score": round(float(display_score), 2),  # Capped for display
                                "_sort_score": round(float(final_score), 2),  # Uncapped for sorting
                                "snippet": doc.page_content[:200] + "...",
                                "metadata": {
                                    "id": job_id_match,
                                    "title": doc.metadata.get("title"),
                                    "company": doc.metadata.get("company_name"),
                                    "type": "job"
                                }
                            }
                            matches.append(match)
                    else:
                        # Fallback to SQL keyword search if no vector store
                        logger.warning("âš ï¸ No job vector store, falling back to SQL search")
                        jobs = db.query(Job).filter(Job.is_active == True).order_by(Job.created_at.desc()).limit(top_k * 2).all()
                        
                        for job in jobs:
                            job_text = f"{job.title} {job.description or ''} {job.requirements or ''}".lower()
                            query_words = set(query_text.lower().split())
                            job_words = set(job_text.split())
                            overlap = len(query_words & job_words)
                            score = min(overlap * 10, 100)
                            
                            match = {
                                "id": job.id,
                                "job_id": job.id,
                                "title": job.title,
                                "company_name": job.employer.company_name if job.employer else "Unknown",
                                "location": job.location,
                                "job_type": job.job_type,
                                "salary_range": job.salary_range,
                                "base_score": float(score),
                                "bonus_score": 0.0,
                                "final_score": float(score),
                                "snippet": f"Job: {job.title} at {job.employer.company_name if job.employer else 'Unknown'}. {(job.description or '')[:150]}...",
                                "metadata": {"id": job.id, "title": job.title, "type": "job"}
                            }
                            matches.append(match)
                    
                    # Sort by _sort_score (uncapped) and take top_k
                    matches.sort(key=lambda x: x.get("_sort_score", x["final_score"]), reverse=True)
                    
                    # Deduplicate: keep only one job per (title, company) combination
                    seen_jobs = {}  # (title_lower, company_lower) -> match dict
                    for match in matches:
                        title = match.get("title", "").lower().strip()
                        company = match.get("company_name", "").lower().strip()
                        key = (title, company)
                        if key not in seen_jobs:
                            seen_jobs[key] = match
                        elif match.get("_sort_score", match["final_score"]) > seen_jobs[key].get("_sort_score", seen_jobs[key]["final_score"]):
                            seen_jobs[key] = match  # Replace with higher scoring duplicate
                    
                    matches = sorted(seen_jobs.values(), key=lambda x: -x.get("_sort_score", x["final_score"]))[:top_k]
                    
                    result = {
                        "matches": matches,
                        "total": len(matches),
                        "match_type": match_type,
                        "success": True,
                        "search_method": "hybrid_semantic" if job_store else "keyword_fallback",
                        "message": f"Found {len(matches)} unique job opportunities" if matches else "No matching jobs found"
                    }
                    
                    result_json = json.dumps(result)
                    logger.info(f"âœ… Found {len(matches)} unique job matches (after dedup)")
                    
                    # Cache for 15 minutes
                    tool_cache.set(
                        "MatchingTool",
                        result_json,
                        ttl=900,
                        query=query_text,
                        match_type=match_type,
                        top_k=top_k,
                        job_id=job_id
                    )
                    
                    return result_json
                
                # For job_to_candidates: Use employee vector store
                elif match_type == "job_to_candidates":
                    # Get employee vector store (with Gemini embeddings)
                    vector_store = get_vector_store("employee")
                    
                    if vector_store is None:
                        return json.dumps({
                            "matches": [],
                            "total": 0,
                            "match_type": match_type,
                            "success": False,
                            "error": "Vector store not initialized. Run profile sync first."
                        })
                    
                    # Perform similarity search
                    results = vector_store.similarity_search_with_score(
                        query_text,
                        k=min(top_k * 2, 20)
                    )
                    
                    matches = []
                    
                    # Get job details for restaurant scoring
                    job = None
                    # Use universal threshold by default
                    match_threshold = DEFAULT_MATCH_THRESHOLD
                    
                    # SPECIAL CASE: Lower threshold for direct hiring
                    # Direct hiring uses generic job templates which have low semantic similarity
                    # Rely more on filters (shift, role) and bonuses than semantic matching
                    if job_id is None:
                        match_threshold = 0.20  # 20% for direct hiring
                        logger.info(f"Using lower threshold for direct hiring: {match_threshold}")
                    elif job_id:
                        job = db.query(Job).filter(Job.id == job_id).first()
                        if job and job.match_score_threshold:
                            # Allow job-specific override if set
                            match_threshold = job.match_score_threshold
                    
                    for doc, score in results:
                        employee_id = doc.metadata.get("id")
                        
                        # Fetch employee for filtering
                        employee = db.query(Employee).filter(Employee.id == employee_id).first()
                        if not employee:
                            continue
                        
                        # FILTER 1: Shift requirements (OR logic - match ANY required shift)
                        if shift_requirements:
                            if not employee.shift_preferences:
                                logger.debug(f"Employee {employee_id} filtered: no shift preferences")
                                continue
                            # Check if employee has at least ONE of the required shifts
                            if not any(shift in employee.shift_preferences for shift in shift_requirements):
                                logger.debug(f"Employee {employee_id} filtered: shift mismatch {employee.shift_preferences} vs {shift_requirements}")
                                continue
                        
                        # FILTER 2: Salary expectations (if requirements provided via job or parameters)
                        # Note: salary check would need to be passed as additional parameter
                        # For now, this is handled by the job object if provided
                        
                        # FILTER 3: Experience requirements (if provided)
                        # This would also need to be passed as additional parameter
                        # For now, handled by bonus scoring
                        
                        # Base semantic score (0-40 points) - reduced to give more weight to qualifications
                        base_score = max(0, 40 * (1 - float(score)))
                        
                        # Add role match bonus (+20 points)
                        role_match_bonus = 0
                        if role and doc.metadata.get("role"):
                            employee_role = doc.metadata.get("role", "").lower().strip()
                            requested_role = role.lower().strip()
                            if employee_role == requested_role:
                                role_match_bonus = 20
                                logger.info(f"  +20 (exact role match: {role})")
                            elif requested_role in employee_role or employee_role in requested_role:
                                role_match_bonus = 10
                                logger.info(f"  +10 (partial role match: {employee_role} ~ {requested_role})")
                        
                        # Add keyword overlap bonus (+15 max)
                        keyword_bonus = 0
                        if doc.page_content and query_text:
                            query_words = set(query_text.lower().split())
                            doc_words = set(doc.page_content.lower().split())
                            overlap = len(query_words & doc_words)
                            keyword_bonus = min(overlap * 3, 15)  # Up to 15 points
                            if keyword_bonus > 0:
                                logger.debug(f"  +{keyword_bonus} (keyword overlap: {overlap} words)")
                        
                        # Add restaurant-specific bonuses
                        bonus_score = 0
                        if employee:
                            # Build requirements dict for direct hiring
                            requirements_dict = {
                                'shift_requirements': shift_requirements if shift_requirements else [],
                                'min_experience': None,  # TODO: Extract from query
                                'role': role  # Role for role-based certification/bonus logic
                            }
                            
                            cached_profile = db.query(ProfileCache).filter(
                                ProfileCache.employee_id == employee_id
                            ).first()
                            
                            # Pass both job (if exists) and requirements (for direct hiring)
                            bonus_score = self._calculate_restaurant_bonus(
                                employee, 
                                job=job, 
                                cached_profile=cached_profile,
                                requirements=requirements_dict if not job else None
                            )
                        
                        # Total score: base (40) + role_match (20) + keywords (15) + restaurant bonus (50) = max 125, capped at 100
                        final_score = min(base_score + role_match_bonus + keyword_bonus + bonus_score, 100)
                        
                        # Convert to 0-1 scale for threshold comparison
                        final_score_normalized = final_score / 100
                        
                        # Log score before filtering (for debugging)
                        logger.info(f"Candidate {employee_id} ({employee.full_name if employee else 'Unknown'}): score={final_score_normalized:.2f} (base={base_score:.1f}, bonus={bonus_score:.1f}) vs threshold={match_threshold:.2f}")
                        
                        # Apply threshold filter - only include if meets minimum
                        if final_score_normalized < match_threshold:
                            logger.info(f"  âŒ Filtered: {final_score_normalized:.2f} < {match_threshold:.2f}")
                            continue
                        
                        match = {
                            "id": employee_id or "unknown",
                            "base_score": round(float(base_score), 2),
                            "bonus_score": round(float(bonus_score), 2),
                            "final_score": round(float(final_score), 2),
                            "snippet": doc.page_content[:200] if doc.page_content else "",
                            "metadata": doc.metadata
                        }
                        matches.append(match)
                    
                    # Debug: Log metadata for tie-breaking analysis
                    if len(matches) > 1 and matches[0]["final_score"] == matches[1]["final_score"]:
                        logger.info(f"  🔍 Tie detected! Inspecting metadata for tie-breaking:")
                        for match in matches[:3]:  # Log first 3 for comparison
                            emp_id = match["metadata"].get("employee_id", "unknown")
                            years = match["metadata"].get("years_in_hospitality", "N/A")
                            certs = match["metadata"].get("certifications", [])
                            logger.info(f"     ID {emp_id}: score={match['final_score']}, years={years}, certs={len(certs)}")
                    
                    # Multi-level sorting for deterministic candidate ranking:
                    # 1. Match score (highest first)
                    # 2. Years in hospitality (most experienced first)
                    # 3. Number of certifications (most certified first)
                    # 4. Employee ID (lowest first, for final determinism)
                    matches.sort(key=lambda x: (
                        x["final_score"],
                        x["metadata"].get("years_in_hospitality", 0),
                        len(x["metadata"].get("certifications", [])),
                        -x["metadata"].get("employee_id", 999999)  # Negative for ascending order
                    ), reverse=True)
                    matches = matches[:top_k]
                    
                    filtered_count = len(results) - len(matches)
                    
                    result = {
                        "matches": matches,
                        "total": len(matches),
                        "match_type": match_type,
                        "success": True,
                        "restaurant_scoring_applied": job is not None,
                        "threshold_applied": match_threshold,
                        "filtered_out": filtered_count,
                        "message": f"Found {len(matches)} qualified candidates (filtered {filtered_count} below {int(match_threshold*100)}% threshold)" if matches else f"No candidates met the {int(match_threshold*100)}% threshold"
                    }
                    
                    result_json = json.dumps(result)
                    logger.info(f"âœ… Found {len(matches)} matches for {match_type} (threshold: {match_threshold*100:.0f}%, filtered: {filtered_count})" + 
                               (f" (with restaurant bonuses)" if job else ""))
                    
                    # Cache for 30 minutes
                    tool_cache.set(
                        "MatchingTool",
                        result_json,
                        ttl=1800,
                        query=query_text,
                        match_type=match_type,
                        top_k=top_k,
                        job_id=job_id
                    )
                    
                    return result_json
                
                else:
                    return json.dumps({"error": "Invalid match_type. Use 'job_to_candidates' or 'candidate_to_jobs'"})
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"âŒ Matching error: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e), "matches": [], "success": False})
