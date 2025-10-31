from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import employer_routes, employee_routes, onboarding_routes
from backend.agents.scheduler_agent import SchedulerAgent  # if added
from backend.db.vector_db import init_vector_store
from backend.routes import scheduler

app = FastAPI(title="Manpower Connector Backend")

# Initialize vector DB (Chroma)
init_vector_store()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(employer_routes.router, prefix="/api/employer", tags=["Employer"])
app.include_router(employee_routes.router, prefix="/api/employee", tags=["Employee"])
app.include_router(onboarding_routes.router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(scheduler.router)
# Optional: Scheduler test route
@app.get("/")
async def root():
    return {"message": "🧠 Manpower Connector Backend is running successfully!"}

@app.on_event("startup")
async def startup_event():
    SchedulerAgent().initialize_daily_schedule()
    print("✅ Scheduler initialized successfully.")
