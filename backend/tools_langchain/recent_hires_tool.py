# backend/tools_langchain/recent_hires_tool.py
"""
RecentHiresTool - Query recent accepted offers/hires for an employer.
Enables employers to ask "Who did we hire recently?" without needing specific job_id.
"""

from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from backend.db.sql_db import SessionLocal
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RecentHiresInput(BaseModel):
    """Input schema for RecentHiresTool."""
    employer_id: int = Field(description="Employer ID to fetch hires for")
    days_back: int = Field(
        default=30,
        description="Number of days to look back (default: 30)"
    )
    
    model_config = ConfigDict(extra='forbid')


class RecentHiresTool(BaseTool):
    """
    Retrieves recent accepted offers/hires for an employer.
    
    Use this when employer asks:
    - "Who did we hire recently?"
    - "Show me our recent hires"
    - "List employees we hired this month"
    - "What positions did we fill recently?"
    
    Returns JSON with employee names, positions, hire dates, and salaries.
    """
    
    name: str = "RecentHiresTool"
    description: str = """
    Fetches recent accepted job offers for a specific employer.
    
    Parameters:
    - employer_id (int): The employer ID
    - days_back (int): Days to look back (default: 30)
    
    Returns: JSON with list of recent hires including name, position, date, salary
    
    Example: "Who did we hire in the last 2 weeks?"
    """
    args_schema: Type[BaseModel] = RecentHiresInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        employer_id: int,
        days_back: int = 30
    ) -> str:
        """Fetch recent hires for an employer."""
        db = SessionLocal()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Query accepted offers using raw SQL to avoid enum issues
            query = text("""
                SELECT 
                    e.id as employee_id,
                    e.full_name as employee_name,
                    j.title as position,
                    j.id as job_id,
                    o.salary_offered,
                    o.responded_at as hire_date,
                    a.status as application_status
                FROM offers o
                JOIN applications a ON o.application_id = a.id
                JOIN employees e ON a.employee_id = e.id  
                JOIN jobs j ON a.job_id = j.id
                WHERE j.employer_id = :employer_id
                AND o.status = 'accepted'
                AND o.responded_at >= :cutoff_date
                ORDER BY o.responded_at DESC
            """)
            
            results = db.execute(
                query, 
                {"employer_id": employer_id, "cutoff_date": cutoff_date}
            ).fetchall()
            
            if not results:
                return json.dumps({
                    "success": True,
                    "total_hires": 0,
                    "message": f"No hires found in the last {days_back} days",
                    "hires": []
                })
            
            # Format hire details
            hires_list = []
            for row in results:
                # Handle hire_date - could be datetime or string from SQL
                hire_date = row[5]
                if hire_date:
                    if hasattr(hire_date, 'strftime'):
                        hire_date_str = hire_date.strftime("%Y-%m-%d")
                    else:
                        # Already a string, use first 10 chars (YYYY-MM-DD)
                        hire_date_str = str(hire_date)[:10]
                else:
                    hire_date_str = "Unknown"
                
                hire_data = {
                    "employee_id": row[0],
                    "employee_name": row[1],
                    "position": row[2],
                    "job_id": row[3],
                    "salary": row[4] or "Not specified",
                    "hire_date": hire_date_str,
                    "status": row[6]
                }
                hires_list.append(hire_data)
            
            result = {
                "success": True,
                "total_hires": len(hires_list),
                "days_back": days_back,
                "hires": hires_list
            }
            
            logger.info(f"✅ Retrieved {len(hires_list)} recent hires for employer {employer_id}")
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Error fetching recent hires for employer {employer_id}: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
        finally:
            db.close()
    
    async def _arun(
        self,
        employer_id: int,
        days_back: int = 30
    ) -> str:
        """Async implementation."""
        return self._run(employer_id, days_back)
