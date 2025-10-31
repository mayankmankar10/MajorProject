# backend/tools_langchain/__init__.py
from backend.tools_langchain.resume_parser_tool import ResumeParserTool
from backend.tools_langchain.interview_scheduler_tool import InterviewSchedulerTool
from backend.tools_langchain.profile_analyzer_tool import ProfileAnalyzerTool
from backend.tools_langchain.job_description_enhancer import JobDescriptionEnhancer
from backend.tools_langchain.embedding_generator import EmbeddingGenerator
from backend.tools_langchain.matching_tool import MatchingTool
from backend.tools_langchain.notification_tool import NotificationTool
from backend.tools_langchain.onboarding_tool import OnboardingTool
from backend.tools_langchain.application_tool import ApplicationTool
from backend.tools_langchain.job_finder_tool import JobFinderTool

__all__ = [
    "ResumeParserTool",
    "InterviewSchedulerTool",
    "ProfileAnalyzerTool",
    "JobDescriptionEnhancer",
    "EmbeddingGenerator",
    "MatchingTool",
    "NotificationTool",
    "OnboardingTool",
    "ApplicationTool",
    "JobFinderTool"
]

# Tool registry for easy initialization
def get_all_tools():
    """Get instances of all available tools."""
    return [
        ResumeParserTool(),
        InterviewSchedulerTool(),
        ProfileAnalyzerTool(),
        JobDescriptionEnhancer(),
        EmbeddingGenerator(),
        MatchingTool(),
        NotificationTool(),
        OnboardingTool(),
        ApplicationTool(),
        JobFinderTool()
    ]

def get_employer_tools():
    """Get tools specific to employers."""
    return [
        JobDescriptionEnhancer(),
        MatchingTool(),
        ProfileAnalyzerTool(),
        InterviewSchedulerTool(),
        OnboardingTool(),
        NotificationTool()
    ]

def get_employee_tools():
    """Get tools specific to employees."""
    return [
        ResumeParserTool(),
        JobFinderTool(),
        MatchingTool(),
        ApplicationTool(),
        NotificationTool()
    ]

def get_common_tools():
    """Get tools available to both roles."""
    return [
        NotificationTool(),
        EmbeddingGenerator()
    ]
