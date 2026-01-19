# backend/tools_langchain/profile_analyzer_tool.py
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
import os
import json
import logging
import warnings

logger = logging.getLogger(__name__)

class ProfileAnalyzerInput(BaseModel):
    """Input schema for ProfileAnalyzerTool."""
    profile_data: str = Field(description="JSON string with candidate profile data (skills, experience, education)")

class ProfileAnalyzerTool(BaseTool):
    """
    DEPRECATED: Use HybridProfileAnalyzer instead for 3-5x faster performance.
    
    Analyzes candidate profiles using GPT-4 to generate comprehensive summaries and insights.
    """
    name: str = "ProfileAnalyzerTool"
    description: str = """
    DEPRECATED: Use HybridProfileAnalyzer for better performance.
    
    Analyzes a candidate's profile using AI to generate insights, summaries, and recommendations.
    
    Input: profile_data (JSON string) - Contains skills, experience, education, certifications
    Output: JSON with professional_summary, strengths, areas_for_growth, role_recommendations
    
    Use this when you need to understand a candidate's profile deeply or generate hiring insights.
    """
    args_schema: Type[BaseModel] = ProfileAnalyzerInput
    llm: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        warnings.warn(
            "ProfileAnalyzerTool is deprecated. Use HybridProfileAnalyzer instead for 3-5x faster performance and 70% cost reduction.",
            DeprecationWarning,
            stacklevel=2
        )
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_REASONING", "gpt-4o"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _run(self, profile_data: str) -> str:
        """Analyze candidate profile."""
        try:
            # Parse profile data
            try:
                profile = json.loads(profile_data)
            except:
                profile = {"raw": profile_data}
            
            prompt = f"""Analyze this candidate profile and provide structured insights:

Profile Data:
{json.dumps(profile, indent=2)}

Provide:
1. Professional Summary (2-3 sentences)
2. Key Strengths (3-5 points)
3. Areas for Growth (2-3 points)
4. Recommended Roles (3-5 role titles)
5. Experience Level Assessment (Junior/Mid/Senior)

Return as JSON with keys: professional_summary, strengths (array), areas_for_growth (array), recommended_roles (array), experience_level"""
            
            response = self.llm.invoke(prompt)
            content = response.content
            
            # Try to parse JSON from response
            try:
                # Extract JSON if wrapped in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
            except:
                result = {
                    "professional_summary": content[:500],
                    "strengths": ["Analysis completed - see summary"],
                    "areas_for_growth": [],
                    "recommended_roles": [],
                    "experience_level": "Unknown"
                }
            
            logger.info(f"✅ Profile analyzed successfully")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Profile analysis error: {str(e)}")
            return json.dumps({"error": str(e), "professional_summary": "Analysis failed"})
    
    async def _arun(self, profile_data: str) -> str:
        """Async implementation."""
        return self._run(profile_data)
