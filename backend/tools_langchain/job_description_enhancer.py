# backend/tools_langchain/job_description_enhancer.py
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from typing import Type
from pydantic import BaseModel, Field
import os
import json
import logging

logger = logging.getLogger(__name__)

class JobDescriptionEnhancerInput(BaseModel):
    """Input schema for JobDescriptionEnhancer."""
    job_title: str = Field(description="Job title")
    raw_description: str = Field(description="Original job description text")
    company_name: str = Field(default="", description="Company name (optional)")

class JobDescriptionEnhancer(BaseTool):
    """
    Enhances job descriptions using GPT-4 Turbo to make them more attractive and comprehensive.
    """
    name: str = "JobDescriptionEnhancer"
    description: str = """
    Enhances job descriptions to make them more professional, comprehensive, and appealing.
    Uses AI to improve clarity, structure, and attractiveness while preserving key requirements.
    
    Input:
    - job_title (string): The job title
    - raw_description (string): Original job description
    - company_name (string, optional): Company name
    
    Output: JSON with enhanced_description, key_requirements (array), and benefits (array)
    
    Use this when posting a new job or improving an existing job description.
    """
    args_schema: Type[BaseModel] = JobDescriptionEnhancerInput
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_ENHANCEMENT", "gpt-4-turbo"),
            temperature=0.5,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _run(self, job_title: str, raw_description: str, company_name: str = "") -> str:
        """Enhance job description."""
        try:
            company_info = f" at {company_name}" if company_name else ""
            
            prompt = f"""Enhance this job description for a {job_title} position{company_info}.

Original Description:
{raw_description}

Create an improved version that:
1. Is clear, professional, and engaging
2. Highlights key responsibilities and requirements
3. Includes potential benefits and growth opportunities
4. Uses inclusive language
5. Is well-structured with sections

Return JSON with:
- enhanced_description (full enhanced text)
- key_requirements (array of 5-7 main requirements)
- benefits (array of 3-5 benefits/perks)
- required_skills (array of technical skills)
- soft_skills (array of soft skills)"""
            
            response = self.llm.invoke(prompt)
            content = response.content
            
            # Parse JSON response
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
            except:
                result = {
                    "enhanced_description": content,
                    "key_requirements": ["See enhanced description"],
                    "benefits": [],
                    "required_skills": [],
                    "soft_skills": []
                }
            
            logger.info(f"✅ Job description enhanced for: {job_title}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Job description enhancement error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "enhanced_description": raw_description,
                "key_requirements": []
            })
    
    async def _arun(self, job_title: str, raw_description: str, company_name: str = "") -> str:
        """Async implementation."""
        return self._run(job_title, raw_description, company_name)
