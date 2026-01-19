# backend/orchestration/workflows/__init__.py
"""
Workflow templates for common multi-step processes.
These serve as predefined sequences of tool calls for complex operations.
"""

# Employer workflows
EMPLOYER_JOB_POSTING_WORKFLOW = {
    "name": "job_posting",
    "steps": [
        {"tool": "JobDescriptionEnhancer", "description": "Enhance JD with GPT-4"},
        {"tool": "EmbeddingGenerator", "description": "Generate embeddings"},
        {"tool": "NotificationTool", "description": "Notify about new posting"}
    ]
}

EMPLOYER_CANDIDATE_SCREENING_WORKFLOW = {
    "name": "candidate_screening",
    "steps": [
        {"tool": "MatchingTool", "description": "Find top candidates"},
        {"tool": "FilterTool", "description": "Apply eligibility filters"},
        {"tool": "ProfileAnalyzerTool", "description": "Analyze profiles"},
        {"tool": "NotificationTool", "description": "Notify about matches"}
    ]
}

EMPLOYER_INTERVIEW_SCHEDULING_WORKFLOW = {
    "name": "interview_scheduling",
    "steps": [
        {"tool": "InterviewSchedulerTool", "description": "Schedule interview"},
        {"tool": "NotificationTool", "description": "Notify candidate and employer"}
    ]
}

EMPLOYER_ONBOARDING_WORKFLOW = {
    "name": "onboarding",
    "steps": [
        {"tool": "OnboardingTool", "description": "Generate offer letter"},
        {"tool": "OnboardingTool", "description": "Generate NDA"},
        {"tool": "ChecklistGenerator", "description": "Create task list"},
        {"tool": "NotificationTool", "description": "Notify new hire"}
    ]
}

# Employee workflows
EMPLOYEE_JOB_SEARCH_WORKFLOW = {
    "name": "job_search",
    "steps": [
        {"tool": "JobFinderTool", "description": "Semantic job search"},
        {"tool": "JobRecommenderTool", "description": "Get personalized recommendations"},
        {"tool": "MatchingTool", "description": "Calculate match scores"}
    ]
}

EMPLOYEE_APPLICATION_WORKFLOW = {
    "name": "job_application",
    "steps": [
        {"tool": "ResumeParserTool", "description": "Parse resume"},
        {"tool": "EmbeddingGenerator", "description": "Generate profile embeddings"},
        {"tool": "JobApplicationTool", "description": "Submit application"},
        {"tool": "NotificationTool", "description": "Confirm submission"}
    ]
}

EMPLOYEE_PROFILE_SETUP_WORKFLOW = {
    "name": "profile_setup",
    "steps": [
        {"tool": "ResumeParserTool", "description": "Extract resume data"},
        {"tool": "ProfileAnalyzerTool", "description": "Analyze skills"},
        {"tool": "EmbeddingGenerator", "description": "Create embeddings"},
        {"tool": "NotificationTool", "description": "Welcome notification"}
    ]
}

# All workflows registry
WORKFLOWS = {
    "employer": {
        "job_posting": EMPLOYER_JOB_POSTING_WORKFLOW,
        "candidate_screening": EMPLOYER_CANDIDATE_SCREENING_WORKFLOW,
        "interview_scheduling": EMPLOYER_INTERVIEW_SCHEDULING_WORKFLOW,
        "onboarding": EMPLOYER_ONBOARDING_WORKFLOW
    },
    "employee": {
        "job_search": EMPLOYEE_JOB_SEARCH_WORKFLOW,
        "job_application": EMPLOYEE_APPLICATION_WORKFLOW,
        "profile_setup": EMPLOYEE_PROFILE_SETUP_WORKFLOW
    }
}

def get_workflow(role: str, workflow_name: str):
    """Get workflow template by role and name."""
    return WORKFLOWS.get(role, {}).get(workflow_name)
