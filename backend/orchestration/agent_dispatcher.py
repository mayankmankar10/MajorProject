# backend/orchestration/agent_dispatcher.py
from typing import List, Dict, Any
from backend.orchestration.orchestrator import SmartServeOrchestrator
import logging

logger = logging.getLogger(__name__)

class AgentDispatcher:
    """
    Manages orchestrator instances and routes requests to appropriate agent based on user role.
    """
    
    def __init__(self, all_tools: Dict[str, List[Any]]):
        """
        Initialize dispatcher with tool sets for different roles.
        
        Args:
            all_tools: Dict mapping role names to lists of tools
                      e.g., {"employer": [tool1, tool2], "employee": [tool3, tool4], "common": [tool5]}
        """
        self.all_tools = all_tools
        self.orchestrators: Dict[str, SmartServeOrchestrator] = {}
        
        # Initialize orchestrators for each role
        self._initialize_orchestrators()
        
        logger.info(f"✅ AgentDispatcher initialized with {len(self.orchestrators)} orchestrators")
    
    def _initialize_orchestrators(self):
        """Create orchestrator instances for each user role."""
        common_tools = self.all_tools.get("common", [])
        
        # Employer orchestrator
        employer_tools = common_tools + self.all_tools.get("employer", [])
        self.orchestrators["employer"] = SmartServeOrchestrator(
            tools=employer_tools,
            user_role="employer"
        )
        
        # Employee orchestrator
        employee_tools = common_tools + self.all_tools.get("employee", [])
        self.orchestrators["employee"] = SmartServeOrchestrator(
            tools=employee_tools,
            user_role="employee"
        )
        
        logger.info(f"Employer tools: {len(employer_tools)}, Employee tools: {len(employee_tools)}")
    
    async def dispatch(
        self,
        user_input: str,
        user_role: str,
        user_id: int,  # Add user_id parameter
        session_id: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatch user command to appropriate orchestrator.
        
        Args:
            user_input: Natural language command
            user_role: "employer" or "employee"
            user_id: User ID making the request
            session_id: Unique session ID
            chat_history: Previous conversation messages
            
        Returns:
            Result dictionary from orchestrator execution
        """
        if user_role not in self.orchestrators:
            logger.error(f"Invalid user role: {user_role}")
            return {
                "output": f"Invalid user role: {user_role}. Must be 'employer' or 'employee'.",
                "success": False,
                "error": "Invalid role"
            }
        
        orchestrator = self.orchestrators[user_role]
        logger.info(f"📬 Dispatching to {user_role} orchestrator")
        
        result = await orchestrator.execute(
            user_input=user_input,
            user_id=user_id,  # Pass user_id to orchestrator
            session_id=session_id,
            chat_history=chat_history
        )
        
        return result
    
    def get_tools_for_role(self, role: str) -> List[Dict[str, str]]:
        """Get available tools for a specific role."""
        if role not in self.orchestrators:
            return []
        return self.orchestrators[role].get_available_tools()
    
    def reload_orchestrator(self, role: str):
        """Reload orchestrator for a specific role (useful for tool updates)."""
        if role == "employer":
            employer_tools = self.all_tools.get("common", []) + self.all_tools.get("employer", [])
            self.orchestrators["employer"] = SmartServeOrchestrator(
                tools=employer_tools,
                user_role="employer"
            )
        elif role == "employee":
            employee_tools = self.all_tools.get("common", []) + self.all_tools.get("employee", [])
            self.orchestrators["employee"] = SmartServeOrchestrator(
                tools=employee_tools,
                user_role="employee"
            )
        logger.info(f"🔄 Reloaded {role} orchestrator")


# Global dispatcher instance (initialized in main.py)
dispatcher: AgentDispatcher = None

def initialize_dispatcher(all_tools: Dict[str, List[Any]]) -> AgentDispatcher:
    """Initialize global dispatcher instance."""
    global dispatcher
    dispatcher = AgentDispatcher(all_tools)
    return dispatcher

def get_dispatcher() -> AgentDispatcher:
    """Get global dispatcher instance."""
    if dispatcher is None:
        raise RuntimeError("Dispatcher not initialized. Call initialize_dispatcher first.")
    return dispatcher
