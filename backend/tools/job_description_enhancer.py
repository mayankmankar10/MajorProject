# backend/tools/job_description_enhancer.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class JobDescriptionInput(BaseModel):
    """Input schema for JobDescriptionEnhancer."""
    title: str = Field(description="Job title")
    description: str = Field(description="Original job description")
    requirements: Optional[str] = Field(None, description="Specific requirements to emphasize")


class JobDescriptionEnhancer(BaseTool):
    """Tool for enhancing job descriptions using GPT-4 Turbo."""
    
    name: str = "enhance_job_description"
    description: str = """
    Enhance and improve a job description for clarity, completeness, and attractiveness.
    Use this when an employer posts a new job to:
    - Improve grammar and readability
    - Add structure and formatting
    - Highlight key requirements and benefits
    - Make the description more appealing to candidates
    - Ensure industry-standard sections are included
    
    Returns the enhanced job description text.
    """
    args_schema: type[BaseModel] = JobDescriptionInput
    
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL_ENHANCEMENT", "gpt-4-turbo")
    
    def _run(
        self, 
        title: str, 
        description: str,
        requirements: Optional[str] = None
    ) -> dict:
        """Enhance job description using GPT-4 Turbo."""
        try:
            # Build prompt
            prompt = f"""You are a professional recruiter and job description writer. Enhance the following job posting to make it clear, complete, and attractive to qualified candidates.

Job Title: {title}

Original Description:
{description}
"""
            
            if requirements:
                prompt += f"\n\nSpecific Requirements to Include:\n{requirements}"
            
            prompt += """

Please enhance this job description by:
1. Improving clarity and readability
2. Adding proper structure (Overview, Responsibilities, Requirements, Benefits)
3. Highlighting key qualifications and skills
4. Making it more engaging and professional
5. Ensuring all essential information is included

Return ONLY the enhanced job description text, without any preamble or explanation."""

            # Call GPT-4 Turbo
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert job description writer who creates clear, comprehensive, and engaging job postings."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            enhanced_description = response.choices[0].message.content.strip()
            
            logger.info(f"Enhanced job description for: {title}")
            
            return {
                "status": "success",
                "enhanced_description": enhanced_description,
                "original_length": len(description),
                "enhanced_length": len(enhanced_description),
                "model": self.model
            }
        
        except Exception as e:
            logger.error(f"Job description enhancement error: {e}")
            return {
                "status": "error",
                "message": f"Failed to enhance job description: {str(e)}",
                "fallback_description": description  # Return original if enhancement fails
            }
    
    async def _arun(self, *args, **kwargs) -> dict:
        """Async version - calls sync implementation."""
        return self._run(*args, **kwargs)
