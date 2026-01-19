"""
Job Posting Creator Tool - Creates public job listings via chat
Handles: "Create a job posting for X", "Post a job for Y positions"
"""

from langchain.tools import BaseTool
from typing import Type, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Job, JobCategory
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class JobPostingCreatorInput(BaseModel):
    """Input schema for job posting creation."""
    employer_input: str = Field(
        description="Natural language job posting request (e.g., 'Create a job posting for 3 waiters in Mumbai')"
    )
    employer_id: int = Field(description="ID of the employer creating the job")
    additional_context: Dict = Field(
        default={},
        description="Additional context like cuisine_type, shift_type, salary_range"
    )

class JobPostingCreatorTool(BaseTool):
    """
    Creates public job postings in the database.
    
    This tool ONLY creates job listings - it does NOT:
    - Match candidates
    - Send offers
    - Create applications
    
    Use this when employer wants to create a job posting for public viewing.
    For direct hiring (immediate need), use BulkHiringWorkflowTool instead.
    """
    name: str = "JobPostingCreatorTool"
    description: str = """
    Create public job postings in the database.
    
    Use when employer says:
    - "Create a job posting for..."
    - "Post a job for..."
    - "I want to list a position for..."
    
    DO NOT use for immediate hiring needs like "I need 5 waiters now".
    
    Input: Natural language request like "Create a job posting for 3 waiters in Mumbai"
    
    Output: Created job details with job_id and posting information.
    """
    args_schema: Type[BaseModel] = JobPostingCreatorInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    async def _arun(self, employer_input: str, employer_id: int, additional_context: dict = None) -> str:
        """
        Create job postings from natural language input.
        
        Returns JSON with:
        {
            "success": bool,
            "jobs_created": int,
            "job_details": [...],
            "message": str
        }
        """
        start_time = datetime.utcnow()
        additional_context = additional_context or {}
        
        logger.info(f"📝 Creating job posting for employer {employer_id}")
        
        try:
            from backend.tools_langchain.position_parser_tool import PositionParserTool
            from backend.tools_langchain.job_templates import get_template, enhance_template
            
            # STEP 1: Parse positions from natural language
            logger.info("📋 Step 1: Parsing job requirements...")
            parser = PositionParserTool()
            parse_result = json.loads(await parser._arun(employer_input))
            
            if not parse_result.get("success"):
                raise Exception(f"Position parsing failed: {parse_result.get('error')}")
            
            positions = parse_result["positions"]
            location = parse_result.get("location") or additional_context.get("location")
            logger.info(f"  Found {len(positions)} positions to post in {location or 'unspecified location'}")
            
            # STEP 2: Load and enhance templates for each position
            logger.info("📝 Step 2: Enhancing job descriptions...")
            enhanced_jobs = []
            for position in positions:
                template = get_template(position["job_type"])
                if not template:
                    logger.warning(f"  No template for {position['job_type']}, using basic")
                    template = {"title": position["title"], "base_description": "Restaurant position"}
                
                # Enhance with context
                enhanced = enhance_template(
                    position["job_type"],
                    location=location,
                    cuisine_type=additional_context.get("cuisine_type"),
                    shift_type=additional_context.get("shift_type"),
                    quantity_needed=position["quantity"]
                )
                
                enhanced_jobs.append({
                    **position,
                    **enhanced,
                    "employer_id": employer_id
                })
            
            # STEP 3: Create jobs in database
            logger.info("💼 Step 3: Creating job postings in database...")
            db = SessionLocal()
            created_jobs = []
            
            # Map job type strings to JobCategory enums
            job_category_map = {
                "waiter": JobCategory.WAITER,
                "cook": JobCategory.COOK,
                "chef": JobCategory.CHEF,
                "bartender": JobCategory.BARTENDER,
                "host": JobCategory.HOST,
                "dishwasher": JobCategory.DISHWASHER
            }
            
            try:
                for job_data in enhanced_jobs:
                    # Get job category string from template and convert to enum
                    job_category_str = job_data.get("job_category", "other")
                    job_category_enum = job_category_map.get(job_category_str.lower(), JobCategory.OTHER)
                    
                    job = Job(
                        employer_id=employer_id,
                        title=job_data["title"],
                        description=job_data.get("enhanced_description") or job_data.get("base_description"),
                        location=location,
                        job_category=job_category_enum,
                        cuisine_type=additional_context.get("cuisine_type"),
                        shift_type=additional_context.get("shift_type"),
                        requires_food_safety=job_data.get("requires_food_safety", True),
                        requires_alcohol_cert=job_data.get("requires_alcohol_cert", False),
                        min_hospitality_experience=job_data.get("min_experience", 0),
                        quantity_needed=job_data["quantity"],
                        requirements={"skills": job_data.get("required_skills", [])},
                        is_active=True
                    )
                    db.add(job)
                    db.flush()  # Get job ID
                    
                    created_jobs.append({
                        "job_id": job.id,
                        "title": job.title,
                        "quantity_needed": job.quantity_needed,
                        "location": location,
                        "job_category": job_category_str
                    })
                
                db.commit()
                logger.info(f"✅ Created {len(created_jobs)} job postings")
            
            finally:
                db.close()
            
            # Final result
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "jobs_created": len(created_jobs),
                "job_details": created_jobs,
                "message": f"Successfully created {len(created_jobs)} job posting(s). They are now visible to candidates.",
                "execution_time_ms": round(duration, 2)
            }
            
            logger.info(f"🎉 Job posting creation complete in {duration:.0f}ms")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Job posting creation error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return json.dumps({
                "success": False,
                "error": str(e),
                "execution_time_ms": round(duration, 2)
            })
    
    def _run(self, employer_input: str, employer_id: int, additional_context: Dict = {}) -> str:
        """Sync wrapper."""
        import asyncio
        return asyncio.run(self._arun(employer_input, employer_id, additional_context))
