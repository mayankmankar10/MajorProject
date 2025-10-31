# backend/orchestration/orchestrator.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict, Any, Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SmartServeOrchestrator:
    """
    Central orchestrator for SmartServe AI agent system.
    Uses LangChain AgentExecutor to manage tool execution and workflow routing.
    """
    
    def __init__(self, tools: List[Any], user_role: str = "employee"):
        """
        Initialize orchestrator with tools and user role context.
        
        Args:
            tools: List of LangChain BaseTool instances
            user_role: "employer" or "employee" for context-aware responses
        """
        self.tools = tools
        self.user_role = user_role
        
        # Initialize GPT-4o for reasoning
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_REASONING", "gpt-4o"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create system prompt based on role
        self.system_prompt = self._create_system_prompt(user_role)
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        logger.info(f"✅ SmartServeOrchestrator initialized for {user_role} with {len(tools)} tools")
    
    def _create_system_prompt(self, role: str) -> str:
        """Create role-specific system prompt."""
        base_prompt = """You are SmartServe AI, an intelligent assistant for workforce recruitment and job matching.
You have access to specialized tools to help users with their tasks.

Your responsibilities:
- Understand user intent from natural language
- Select and execute appropriate tools
- Provide clear, actionable responses
- Handle errors gracefully
- Maintain professional yet friendly tone
"""
        
        if role == "employer":
            return base_prompt + """
You are assisting an EMPLOYER. Focus on:
- Posting and managing job listings
- Reviewing and screening candidates
- Scheduling interviews
- Managing the hiring pipeline
- Generating onboarding documents

Always prioritize employer needs and efficiency."""
        
        elif role == "employee":
            return base_prompt + """
You are assisting an EMPLOYEE/JOB SEEKER. Focus on:
- Finding relevant job opportunities
- Getting personalized job recommendations
- Applying to jobs
- Tracking application status
- Preparing for interviews

Always prioritize candidate experience and career growth."""
        
        return base_prompt
    
    async def execute(
        self, 
        user_input: str, 
        session_id: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute user command through agent orchestration.
        
        Args:
            user_input: Natural language command from user
            session_id: Unique session identifier
            chat_history: Previous conversation context
            
        Returns:
            Dict with output, intermediate_steps, and metadata
        """
        try:
            logger.info(f"🤖 Orchestrator processing: '{user_input}' for session {session_id}")
            
            # Prepare chat history
            history = []
            if chat_history:
                for msg in chat_history[-5:]:  # Keep last 5 messages for context
                    if msg["role"] == "user":
                        history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        history.append(SystemMessage(content=msg["content"]))
            
            # Execute agent
            result = await self.agent_executor.ainvoke({
                "input": user_input,
                "chat_history": history
            })
            
            logger.info(f"✅ Orchestrator completed successfully")
            
            return {
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {str(e)}")
            return {
                "output": f"I encountered an error processing your request: {str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools with descriptions."""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]
