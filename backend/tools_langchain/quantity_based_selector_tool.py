"""
Quantity-Based Selector Tool - Smart candidate selection with quantity constraints
Ensures exact N candidates selected per position without overlap
"""

from langchain.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import json
import logging

logger = logging.getLogger(__name__)

class QuantityBasedSelectorInput(BaseModel):
    """Input schema for quantity-based selection."""
    positions: List[Dict] = Field(
        description="List of positions with requirements: [{'job_type': 'waiter', 'quantity': 5, 'matches': [...]}]"
    )

class QuantityBasedSelectorTool(BaseTool):
    """
    Selects exactly N top candidates per position without overlap.
    
    Key features:
    - Respects quantity requirements per job type
    - Prevents duplicate selection (same candidate for multiple positions)
    - Prioritizes filling smaller quantities first
    - Handles insufficient candidate scenarios
    """
    name: str = "QuantityBasedSelectorTool"
    description: str = """
    Intelligently selects exact number of candidates per position type without overlap.
    
    Input: List of positions with:
    - job_type: Position category (waiter, cook, chef, etc.)
    - quantity: Number of candidates needed
    - matches: Array of candidate matches with scores
    
    Output: Selected candidates per position with selected IDs tracked
    
    Algorithm:
    1. Sort positions by quantity (fill smaller needs first)
    2. For each position, select top N candidates not already selected
    3. Track selections to prevent overlap
    4. Report unfilled positions if insufficient candidates
    
    Example:
    Input: [
        {"job_type": "waiter", "quantity": 5, "matches": [...]},
        {"job_type": "cook", "quantity": 2, "matches": [...]}
    ]
    Output: {"waiter": [5 candidates], "cook": [2 candidates], "unfilled": []}
    """
    args_schema: Type[BaseModel] = QuantityBasedSelectorInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(self, positions: List[Dict]) -> str:
        """
        Select candidates based on quantity requirements.
        
        Returns JSON with:
        {
            "selections": {"job_type": [selected_candidates]},
            "total_selected": int,
            "unfilled": [{"job_type": str, "needed": int, "found": int}]
        }
        """
        try:
            selections = {}
            already_selected_ids = set()
            unfilled = []
            total_selected = 0
            
            # Sort positions by quantity (fill smaller requirements first to maximize coverage)
            sorted_positions = sorted(positions, key=lambda p: p.get("quantity", 0))
            
            logger.info(f"📊 Selecting candidates for {len(sorted_positions)} positions")
            
            for position in sorted_positions:
                job_type = position.get("job_type")
                quantity = position.get("quantity", 1)
                matches = position.get("matches", [])
                
                logger.info(f"  Processing {job_type}: need {quantity} candidates from {len(matches)} matches")
                
                selected_for_position = []
                
                # Select top N candidates not already selected
                for candidate in matches:
                    candidate_id = candidate.get("id")
                    
                    # Skip if already selected for another position
                    if candidate_id in already_selected_ids:
                        continue
                    
                    # Add to selection
                    selected_for_position.append(candidate)
                    already_selected_ids.add(candidate_id)
                    
                    # Stop when we have enough
                    if len(selected_for_position) == quantity:
                        break
                
                selections[job_type] = selected_for_position
                total_selected += len(selected_for_position)
                
                # Track unfilled positions
                if len(selected_for_position) < quantity:
                    unfilled.append({
                        "job_type": job_type,
                        "needed": quantity,
                        "found": len(selected_for_position),
                        "shortfall": quantity - len(selected_for_position)
                    })
                    logger.warning(f"  ⚠️  {job_type}: Only found {len(selected_for_position)}/{quantity} candidates")
                else:
                    logger.info(f"  ✅ {job_type}: Selected {len(selected_for_position)}/{quantity} candidates")
            
            result = {
                "success": True,
                "selections": selections,
                "total_selected": total_selected,
                "unfilled": unfilled,
                "summary": {
                    job_type: len(candidates) 
                    for job_type, candidates in selections.items()
                }
            }
            
            logger.info(f"🎯 Selection complete: {total_selected} total candidates selected")
            if unfilled:
                logger.warning(f"⚠️  {len(unfilled)} positions partially unfilled")
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Selection error: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({"success": False, "error": str(e)})
    
    async def _arun(self, positions: List[Dict]) -> str:
        """Async implementation."""
        return self._run(positions)
