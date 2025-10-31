from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import (
    auth_routes,
    notification_routes,
    employer_routes,
    employee_routes,
    onboarding_routes,
    scheduler,
    analytics_routes,
    tool_routes
)
from backend.chat import router as chat_router
from backend.db.vector_db import init_vector_store
from backend.db.sql_db import init_sql_db
from backend.orchestration import initialize_dispatcher
from backend.tools_langchain import get_employer_tools, get_employee_tools, get_common_tools
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="SmartServe - AI-Powered Recruitment Platform",
    description="Multi-agent AI platform for automated workforce recruitment and job matching",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "🚀 SmartServe API is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "vector_store": "initialized"
    }

# Register routes
app.include_router(auth_routes.router)
app.include_router(notification_routes.router)
app.include_router(employer_routes.router, prefix="/api/employer", tags=["Employer"])
app.include_router(employee_routes.router, prefix="/api/employee", tags=["Employee"])
app.include_router(onboarding_routes.router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["Scheduler"])
app.include_router(analytics_routes.router, tags=["Analytics"])
app.include_router(tool_routes.router)
app.include_router(chat_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 Starting SmartServe application...")
    
    # Initialize databases
    try:
        init_sql_db()
        logger.info("✅ SQL database initialized")
    except Exception as e:
        logger.error(f"❌ SQL database initialization failed: {e}")
    
    try:
        init_vector_store()
        logger.info("✅ Vector store initialized")
    except Exception as e:
        logger.error(f"❌ Vector store initialization failed: {e}")
    
    # Initialize orchestration layer
    try:
        common_tools = get_common_tools()
        employer_tools = get_employer_tools()
        employee_tools = get_employee_tools()
        
        all_tools = {
            "common": common_tools,
            "employer": employer_tools,
            "employee": employee_tools
        }
        
        initialize_dispatcher(all_tools)
        logger.info("✅ Orchestration layer initialized")
        logger.info(f"   - Common tools: {len(common_tools)}")
        logger.info(f"   - Employer tools: {len(employer_tools)}")
        logger.info(f"   - Employee tools: {len(employee_tools)}")
    except Exception as e:
        logger.error(f"❌ Orchestration initialization failed: {e}")
    
    # Log configuration
    logger.info(f"Frontend URL: {frontend_url}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info("✅ SmartServe started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Shutting down SmartServe application")
