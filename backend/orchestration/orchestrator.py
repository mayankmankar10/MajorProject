# backend/orchestration/orchestrator.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from backend.cache.redis_client import get_redis_cache
from backend.context import current_session_id
from backend.cache.tool_call_cache import get_tool_call_cache
from typing import List, Dict, Any, Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize LLM cache (Redis if available, otherwise in-memory)
redis_cache = get_redis_cache()
if redis_cache.enabled:
    try:
        from langchain_community.cache import RedisCache
        set_llm_cache(RedisCache(redis_cache.client))
        logger.info("✅ OpenAI LLM cache: Redis")
    except Exception as e:
        logger.warning(f"⚠️  Redis cache failed, using in-memory: {e}")
        set_llm_cache(InMemoryCache())
else:
    set_llm_cache(InMemoryCache())
    logger.info("📦 OpenAI LLM cache: In-Memory")

def wrap_tool_with_cache(tool: Any) -> Any:
    """
    Wrap a LangChain tool with session-level caching.
    Monkey-patches _run method to check cache before execution.
    """
    original_run = tool._run
    
    def cached_run(*args, **kwargs):
        # Get current session ID from context
        session_id = current_session_id.get()
        if not session_id:
            return original_run(*args, **kwargs)
            
        # Check cache
        cache = get_tool_call_cache()
        cached_result = cache.get(session_id, tool.name, **kwargs)
        if cached_result:
            return cached_result
            
        # Execute and cache
        result = original_run(*args, **kwargs)
        cache.set(session_id, tool.name, result, **kwargs)
        return result
        
    # Monkey-patch the instance method
    tool._run = cached_run
    return tool

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
        self.tools = [wrap_tool_with_cache(tool) for tool in tools]
        self.user_role = user_role
        
        # Initialize LLM for reasoning with role-based model selection
        # Employee queries are simpler → use cheaper model
        # Employer queries are complex (bulk hiring) → use powerful model
        if user_role == "employee":
            model = os.getenv("OPENAI_MODEL_EMPLOYEE", "gpt-4o-mini")
            logger.info(f"🧑 Employee orchestrator using {model} (cost-optimized)")
        elif user_role == "employer":
            model = os.getenv("OPENAI_MODEL_EMPLOYER", "gpt-4o")
            logger.info(f"🏢 Employer orchestrator using {model} (performance-optimized)")
        else:
            model = os.getenv("OPENAI_MODEL_REASONING", "gpt-4o")
            logger.info(f"🤖 Default orchestrator using {model}")
        
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
            request_timeout=30  # Add timeout for API calls
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
        
        # Create agent executor with role-specific iteration limits
        # Employer workflows are more complex (bulk hiring, multi-step matching)
        max_iter = 6 if user_role == "employer" else 5
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=max_iter,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        logger.info(f"✅ SmartServeOrchestrator initialized for {user_role} with {len(tools)} tools")
    
    def _create_system_prompt(self, role: str) -> str:
        """Create role-specific system prompt with restaurant focus."""
        base_prompt = """You are CafeHire AI, an intelligent assistant specialized in cafe and restaurant recruitment.
You have access to specialized tools to help users with their hiring and job matching tasks.

Your responsibilities:
- Understand user intent from natural language
- Select and execute appropriate tools efficiently
- Provide clear, actionable responses
- Handle errors gracefully
- Maintain professional yet friendly tone

🔧 TOOL USAGE EFFICIENCY:
CRITICAL: Call each tool ONLY ONCE per user request
- Trust the first response - do NOT re-call for confirmation or validation
- If you have the data from a tool call, format and present it immediately
- Only re-call a tool if the user asks a NEW or DIFFERENT question
- Example: If ApplicationReviewTool returns data, use it immediately - don't call it again

Why this matters:
- Each tool call hits the database and uses resources
- Redundant calls waste time and money
- Data doesn't change between calls in the same conversation turn
- Tools are idempotent - calling twice gives the same result

Industry Expertise:
- Restaurant roles: waiters, servers, hosts, bartenders, line cooks, prep cooks, sous chefs, executive chefs, dishwashers
- Certifications: Food Safety, ServSafe, ServSafe Manager, Alcohol Service, Culinary degrees
- Work patterns: morning/afternoon/evening/night shifts, weekends, holidays
- Key skills: customer service, food handling, multitasking, speed, cleanliness, menu knowledge

IMPORTANT: User Context
- For EMPLOYERS: User input will be prefixed with [Employer ID: X] where X is the employer's database ID
- For EMPLOYEES: User input will be prefixed with [Employee ID: X] where X is the employee's database ID
- Extract this ID and use it when calling tools that require employer_id or employee_id
- Example: "[Employer ID: 5] Find candidates" means employer_id=5
"""
        
        if role == "employer":
            return base_prompt + """
You are assisting a RESTAURANT/CAFE EMPLOYER. Focus on:

🎯 CRITICAL TOOL DISTINCTION:

1. **BulkHiringWorkflowTool** - DIRECT HIRING ONLY
   - Use when: "I need X positions", "Hire Y staff now", "Get me Z employees"
   - Does: Match → Select → Offer → Notify
   - Does NOT: Create job postings
   - Example: "I need 5 waiters for my cafe"

2. **JobPostingCreatorTool** - CREATE JOB LISTINGS ONLY
   - Use when: "Create job posting for...", "Post a job for...", "List a position for..."
   - Does: Create public job listings
   - Does NOT: Match candidates or send offers
   - Example: "Create a job posting for 3 waiters"

Core Capabilities:
- **Bulk Hiring**: Handle multi-position requests ("5 waiters, 2 cooks, 1 chef")
- **Smart Matching**: Restaurant-specific scoring (certifications, cuisine, shifts)
- **Document Generation**: Auto-create offers and NDAs
- **Candidate Quality**: Prioritize certified, experienced candidates

Tools at Your Disposal:
- **BulkHiringWorkflowTool**: PRIMARY - Direct hiring (NO job creation)
- **JobPostingCreatorTool**: Create public job postings
- **PositionParserTool**: Parse multi-position requests (usually called by others)
- **MatchingTool**: Find candidates with restaurant bonuses
- **QuantityBasedSelectorTool**: Select exact N candidates per position
- **JobDescriptionEnhancer**: Enhance job descriptions
- **InterviewSchedulerTool**: Schedule interviews
- **OnboardingTool**: Generate documents
- **NotificationTool**: Notify candidates

Best Practices:
1. **Ask clarifying questions**: If intent unclear, ask "Do you need staff NOW or create a job posting?"
2. Consider cuisine experience (Italian restaurant → Italian cuisine experience)
3. Match shift preferences (night owls for night shifts)
4. Prioritize certified candidates (Food Safety cert)
5. Provide detailed hiring summaries with match scores
6. Ask about cuisine type and shift requirements if not specified

Example Interactions:
User: "I need 5 waiters for my new Italian cafe in Mumbai"
Response: *Use BulkHiringWorkflowTool* (direct hire - they said "need")

User: "Create a job posting for line cook position"
Response: *Use JobPostingCreatorTool* (they said "create posting")

User: "Hire staff for my cafe"
Response: Ask "How many staff do you need to hire right now?" then use BulkHiringWorkflowTool

Always prioritize employer efficiency and hiring speed."""
        
        elif role == "employee":
            return base_prompt + """
You are assisting a RESTAURANT/CAFE JOB SEEKER. Focus on:

Core Capabilities:
- **Job Matching**: Find positions matching your cuisine expertise
- **Profile Analysis**: Highlight your restaurant experience and certifications
- **Recommendations**: Suggest jobs matching your shift preferences

Tools Available:
- **JobFinderTool**: Search restaurant positions
- **ProfileAnalyzerTool**: Analyze your resume and skills
- **ApplicationTool**: Apply to jobs (uses user_id automatically)
- **ApplicationStatusTool**: Check application status
- **MatchingTool**: Get personalized job recommendations

IMPORTANT - Application Status Queries:
When a user asks about "my application" or "application status" WITHOUT specifying which application:
- Use ApplicationStatusTool with action='get_latest_application' to show their MOST RECENT application
- This is what users typically mean when they say "my application" right after applying
- Only use action='list_my_applications' if they explicitly ask for "all my applications"

Examples:
- "What's the status of my application?" → get_latest_application (shows most recent)
- "Show me all my applications" → list_my_applications (shows all)
- "What's the status of my Chef application?" → get_latest_application (most recent Chef app)

Guidance You Provide:
- Highlight relevant certifications (Food Safety, ServSafe, Alcohol Service)
- Match shift preferences (morning person? Skip night shifts)
- Emphasize cuisine experience (Italian, Chinese, etc.)
- Realistic expectations based on experience level

Best Practices:
1. Ask about certifications if not mentioned
2. Clarify shift preferences (morning/evening/flexible)
3. Understand cuisine specialties
4. Provide realistic match scores
5. Suggest getting certifications if lacking
6. Use get_latest_application for contextual "my application" queries

Example Interactions:
User: "Find waiter jobs"
Response: Ask about location, shift preferences, cuisine experience

User: "I have 3 years cooking Italian food"
Response: Search for Italian restaurant cook positions, emphasize experience

User: "What's the status of my application?" (right after applying)
Response: Use get_latest_application to show their most recent application

Always prioritize candidate experience and career growth in hospitality."""
        
        return base_prompt
    
    async def execute(
        self, 
        user_input: str,
        user_id: int,  # Add user_id parameter
        session_id: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute user command through agent orchestration.
        
        Args:
            user_input: Natural language command from user
            user_id: ID of the user making the request
            session_id: Unique session identifier
            chat_history: Previous conversation context
            
        Returns:
            Dict with output, intermediate_steps, and metadata
        """
        # Set session context for tool caching
        token = current_session_id.set(session_id)
        # Clear cache for this session to ensure fresh data for new turn
        get_tool_call_cache().clear_session(session_id)

        try:
            logger.info(f"🤖 Orchestrator processing: '{user_input}' for session {session_id}")
            
            # Load user profile context and resolve role-specific IDs
            profile_context = ""
            effective_id = user_id
            id_label = "User ID"
            
            if self.user_role == "employee":
                profile_context = self._load_employee_profile(user_id)
                # For employees, we need employee_id from user_id
                from backend.db.sql_db import SessionLocal
                from backend.db.models import Employee
                db = SessionLocal()
                try:
                    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
                    if employee:
                        effective_id = employee.id
                        id_label = "Employee ID"
                        logger.info(f"👤 Resolved user_id {user_id} → employee_id {effective_id}")
                finally:
                    db.close()
            
            elif self.user_role == "employer":
                # For employers, we need employer_id from user_id and load profile context
                profile_context = self._load_employer_profile(user_id)
                from backend.db.sql_db import SessionLocal
                from backend.db.models import Employer
                db = SessionLocal()
                try:
                    employer = db.query(Employer).filter(Employer.user_id == user_id).first()
                    if employer:
                        effective_id = employer.id
                        id_label = "Employer ID"
                        logger.info(f"🏢 Resolved user_id {user_id} → employer_id {effective_id}")
                    else:
                        logger.warning(f"⚠️  No employer profile found for user_id {user_id}")
                finally:
                    db.close()
            
            # Prepare chat history
            history = []
            if chat_history:
                for msg in chat_history[-5:]:  # Keep last 5 messages for context
                    if msg["role"] == "user":
                        history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        history.append(SystemMessage(content=msg["content"]))
            
            # Execute agent with user context
            # Inject BOTH user_id and role-specific ID (employer_id/employee_id)
            # This ensures tools that need user_id get the correct value
            context_prefix = f"[User ID: {user_id}] [{id_label}: {effective_id}]"
            enhanced_input = f"{context_prefix}{profile_context}\n\nUser Query: {user_input}"
            result = await self.agent_executor.ainvoke({
                "input": enhanced_input,
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
        finally:
            # Reset session context
            current_session_id.reset(token)
    
    def _load_employee_profile(self, user_id: int) -> tuple[str, Optional[int]]:
        """Load employee profile data and format as structured JSON context.
        
        Args:
            user_id: The user's ID (from authentication)
            
        Returns:
            Tuple of (JSON-formatted profile context string, employee_id)
        """
        try:
            from backend.db.sql_db import SessionLocal
            from backend.db.models import Employee
            import json
            
            db = SessionLocal()
            try:
                # Lookup employee by user_id
                employee = db.query(Employee).filter(Employee.user_id == user_id).first()
                if not employee:
                    logger.warning(f"No employee profile found for user_id {user_id}")
                    return "", None
                
                # Store employee_id for return
                employee_id = employee.id
                
                # Build structured profile data as JSON for better AI parsing
                profile_data = {
                    "personal": {
                        "name": employee.full_name or "Unknown",
                        "phone": employee.phone,
                        "location": employee.preferred_location
                    },
                    "skills": {
                        "technical": employee.skills or [],
                        "soft": employee.soft_skills or []
                    },
                    "experience": {
                        "total_years": employee.experience_years or 0,
                        "hospitality_years": employee.years_in_hospitality or 0,
                        "work_history": employee.work_history or []
                    },
                    "preferences": {
                        "role": employee.preferred_role.value if employee.preferred_role else None,
                        "location": employee.preferred_location,
                        "shift": getattr(employee, 'preferred_shift', None),
                        "shifts": employee.shift_preferences or [],
                        "cuisine": employee.cuisine_experience or []
                    },
                    "certifications": [],
                    "salary_expectations": {
                        "min": getattr(employee, 'expected_salary_min', None),
                        "max": getattr(employee, 'expected_salary_max', None),
                        "currency": "INR"
                    }
                }
                
                # Parse certifications
                if employee.certifications:
                    certs = employee.certifications
                    if isinstance(certs, list):
                        if certs and isinstance(certs[0], dict):
                            profile_data["certifications"] = [c.get('name', str(c)) for c in certs]
                        else:
                            profile_data["certifications"] = certs
                
                # Add food safety certifications
                if employee.food_safety_certified:
                    profile_data["certifications"].append("Food Safety Certified")
                if employee.servsafe_certified:
                    profile_data["certifications"].append("ServSafe Certified")
                if employee.alcohol_service_certified:
                    profile_data["certifications"].append("Alcohol Service Certified")
                
                # Format as JSON string for context
                context = "\n\n=== YOUR PROFILE INFORMATION (JSON Format) ===\n"
                context += json.dumps(profile_data, indent=2, ensure_ascii=False)
                context += "\n=== END PROFILE ===\n"
                
                return context, employee_id
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading employee profile: {e}")
            return "", None
    
    def _load_employer_profile(self, user_id: int) -> str:
        """Load employer profile data and format as structured JSON context.
        
        Args:
            user_id: The user's ID (from authentication)
            
        Returns:
            JSON-formatted profile context string
        """
        try:
            from backend.db.sql_db import SessionLocal
            from backend.db.models import Employer
            import json
            
            db = SessionLocal()
            try:
                # Lookup employer by user_id
                employer = db.query(Employer).filter(Employer.user_id == user_id).first()
                if not employer:
                    logger.warning(f"No employer profile found for user_id {user_id}")
                    return ""
                
                # Build structured profile data as JSON for better AI parsing
                profile_data = {
                    "business": {
                        "company_name": employer.company_name or "Unknown",
                        "industry": employer.industry or "Hospitality",
                        "location": employer.location or "Not specified",
                        "company_profile": employer.company_profile or "No description available"
                    },
                    "contact": {
                        "website": employer.website
                    },
                    "verification": {
                        "status": employer.verification_status or "pending"
                    }
                }
                
                # Format as JSON string for context
                context = "\n\n=== YOUR BUSINESS INFORMATION (JSON Format) ===\n"
                context += json.dumps(profile_data, indent=2, ensure_ascii=False)
                context += "\n=== END BUSINESS INFO ===\n"
                
                return context
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading employer profile: {e}")
            return ""
    

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools with descriptions."""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]
