# backend/routes/tool_routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.utils.auth import get_current_user
from backend.db.models import User
from backend.orchestration import get_dispatcher
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["Tools"])

class ToolInvocation(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

@router.get("/available")
async def get_available_tools(current_user: User = Depends(get_current_user)):
    """Get list of tools available to the current user based on their role."""
    try:
        dispatcher = get_dispatcher()
        tools = dispatcher.get_tools_for_role(current_user.role.value)
        
        return {
            "role": current_user.role.value,
            "tools": tools,
            "total": len(tools)
        }
    except Exception as e:
        logger.error(f"Error fetching tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoke")
async def invoke_tool(
    invocation: ToolInvocation,
    current_user: User = Depends(get_current_user)
):
    """
    Directly invoke a specific tool with parameters.
    This bypasses the orchestrator and calls the tool directly.
    """
    try:
        dispatcher = get_dispatcher()
        
        # Get orchestrator for user role
        orchestrator = dispatcher.orchestrators.get(current_user.role.value)
        if not orchestrator:
            raise HTTPException(status_code=400, detail="Invalid user role")
        
        # Find the tool
        tool = None
        for t in orchestrator.tools:
            if t.name == invocation.tool_name:
                tool = t
                break
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{invocation.tool_name}' not found or not available to your role"
            )
        
        # Invoke tool
        result = await tool._arun(**invocation.parameters)
        
        logger.info(f"Tool {invocation.tool_name} invoked by user {current_user.id}")
        
        return {
            "tool_name": invocation.tool_name,
            "result": result,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Tool invocation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{tool_name}")
async def get_tool_info(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific tool."""
    try:
        dispatcher = get_dispatcher()
        orchestrator = dispatcher.orchestrators.get(current_user.role.value)
        
        if not orchestrator:
            raise HTTPException(status_code=400, detail="Invalid user role")
        
        # Find tool
        tool = None
        for t in orchestrator.tools:
            if t.name == tool_name:
                tool = t
                break
        
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Get tool schema
        return {
            "name": tool.name,
            "description": tool.description,
            "args_schema": tool.args_schema.schema() if tool.args_schema else {},
            "return_direct": getattr(tool, 'return_direct', False)
        }
        
    except Exception as e:
        logger.error(f"Error fetching tool info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
