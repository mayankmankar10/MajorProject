"""
SLM-powered position parser for bulk hiring requests.
Uses local SLM for fast parsing of multi-position hiring requests.
"""
from langchain.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.llm.slm_client import get_slm_client
import json
import logging

logger = logging.getLogger(__name__)

class SLMPositionParserInput(BaseModel):
    """Input schema for SLMPositionParser."""
    hiring_request: str = Field(description="Natural language hiring request (e.g., 'Need 5 waiters and 2 cooks')")

class SLMPositionParser(BaseTool):
    """
    Parse hiring requests into structured positions using local SLM (fast, free).
    
    Uses phi3:mini for instant parsing without API costs.
    """
    name: str = "SLMPositionParser"
    description: str = """
    Parse bulk hiring request into structured positions using local SLM (very fast).
    
    Input:
    - hiring_request (string): Natural language request like "Need 5 waiters, 3 cooks, 2 bartenders"
    
    Output: JSON array of positions with role and quantity
    
    Use this to quickly parse multi-position hiring requests.
    """
    args_schema: Type[BaseModel] = SLMPositionParserInput
    
    # Declare SLM client as excluded field
    slm: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slm = get_slm_client()
    
    def _run(self, hiring_request: str) -> str:
        """Parse positions using SLM."""
        
        # Check if SLM available
        if not self.slm.is_available():
            logger.warning("⚠️  SLM unavailable for position parsing")
            return json.dumps({
                "error": "SLM unavailable",
                "positions": [],
                "success": False,
                "fallback_needed": True
            })
        
        try:
            # Create parsing prompt
            prompt = f"""Parse this hiring request into structured positions.
Return ONLY a JSON array, no other text.

Request: "{hiring_request}"

Output format:
[
  {{"role": "waiter", "quantity": 5, "location": "Mumbai"}},
  {{"role": "cook", "quantity": 3, "location": "Mumbai"}}
]

Common roles: waiter, cook, chef, bartender, host, manager, dishwasher, line cook
Extract quantity and role. If location mentioned, include it."""

            # Invoke SLM
            logger.info("🤖 Using SLM for position parsing...")
            result = self.slm.invoke(prompt, max_tokens=256)
            
            if not result:
                raise Exception("SLM returned empty response")
            
            # Try to parse JSON
            try:
                # Extract JSON from response
                result_clean = result.strip()
                if "```json" in result_clean:
                    result_clean = result_clean.split("```json")[1].split("```")[0]
                elif "```" in result_clean:
                    result_clean = result_clean.split("```")[1].split("```")[0]
                
                positions = json.loads(result_clean)
                
                # Validate structure
                if not isinstance(positions, list):
                    positions = [positions]
                
                result_obj = {
                    "positions": positions,
                    "total_positions": len(positions),
                    "total_hires": sum(p.get("quantity", 0) for p in positions),
                    "success": True,
                    "source": "slm"
                }
                
                logger.info(f"✅ SLM parsed {len(positions)} position types, {result_obj['total_hires']} total hires")
                return json.dumps(result_obj)
                
            except json.JSONDecodeError:
                logger.warning("⚠️  SLM response not valid JSON")
                return json.dumps({
                    "raw_response": result,
                    "success": False,
                    "error": "Invalid JSON from SLM"
                })
                
        except Exception as e:
            logger.error(f"❌ SLM position parsing error: {e}")
            return json.dumps({
                "error": str(e),
                "positions": [],
                "success": False
            })
    
    async def _arun(self, hiring_request: str) -> str:
        """Async implementation."""
        return self._run(hiring_request)
