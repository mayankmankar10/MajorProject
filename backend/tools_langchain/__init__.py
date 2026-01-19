# backend/tools_langchain/__init__.py
from backend.tools_langchain.resume_parser_tool import ResumeParserTool
from backend.tools_langchain.interview_scheduler_tool import InterviewSchedulerTool
from backend.tools_langchain.profile_analyzer_tool import ProfileAnalyzerTool
from backend.tools_langchain.job_description_enhancer import JobDescriptionEnhancer
from backend.tools_langchain.embedding_generator import EmbeddingGenerator
from backend.tools_langchain.matching_tool import MatchingTool
from backend.tools_langchain.notification_tool import NotificationTool
from backend.tools_langchain.onboarding_tool import OnboardingTool
from backend.tools_langchain.job_finder_tool import JobFinderTool
from backend.tools_langchain.job_application_tool import JobApplicationTool

# NEW: Missing critical tools
from backend.tools_langchain.job_posting_tool import JobPostingTool
from backend.tools_langchain.job_listing_tool import JobListingTool
from backend.tools_langchain.application_status_tool import ApplicationStatusTool
from backend.tools_langchain.application_review_tool import ApplicationReviewTool
from backend.tools_langchain.application_comparison_tool import ApplicationComparisonTool

# Restaurant-specific tools
from backend.tools_langchain.position_parser_tool import PositionParserTool
from backend.tools_langchain.bulk_profile_processor_tool import BulkProfileProcessorTool
from backend.tools_langchain.quantity_based_selector_tool import QuantityBasedSelectorTool
from backend.tools_langchain.bulk_hiring_workflow_tool import BulkHiringWorkflowTool
from backend.tools_langchain.job_posting_creator_tool import JobPostingCreatorTool

# Hybrid SLM + GPT-4 tools
from backend.tools_langchain.hybrid_profile_analyzer import HybridProfileAnalyzer
from backend.tools_langchain.slm_skill_extractor import SLMSkillExtractor
from backend.tools_langchain.slm_position_parser import SLMPositionParser

# AI-powered tools (GPT-4)
from backend.tools_langchain.resume_generator_tool import ResumeGeneratorTool

# Offer management tools (Autonomous Hiring Pipeline)
from backend.tools_langchain.offer_acceptance_tool import OfferAcceptanceTool
from backend.tools_langchain.recent_hires_tool import RecentHiresTool

__all__ = [
    "ResumeParserTool",
    "InterviewSchedulerTool",
    "ProfileAnalyzerTool",
    "JobDescriptionEnhancer",
    "EmbeddingGenerator",
    "MatchingTool",
    "NotificationTool",
    "OnboardingTool",
    "JobFinderTool",
    # Missing critical tools
    "JobPostingTool",
    "ApplicationStatusTool",
    # Restaurant-specific
    "PositionParserTool",
    "BulkProfileProcessorTool",
    "QuantityBasedSelectorTool",
    "BulkHiringWorkflowTool",
    "JobPostingCreatorTool",
    # Hybrid SLM + GPT-4
    "HybridProfileAnalyzer",
    "SLMSkillExtractor",
    "SLMPositionParser",
    # AI-powered (GPT-4)
    "ResumeGeneratorTool"
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
        JobFinderTool(),
        # Restaurant-specific
        PositionParserTool(),
        BulkProfileProcessorTool(),
        QuantityBasedSelectorTool(),
        BulkHiringWorkflowTool()
    ]

def get_employer_tools():
    """
    Get tools specific to employers.
    ENHANCED with restaurant-specific bulk hiring capabilities.
    """
    return [
        # PRIMARY: Automated bulk hiring workflow
        BulkHiringWorkflowTool(),  # NEW - Direct hiring (NO job creation)
        JobPostingCreatorTool(),  # NEW - Create job postings via chat
        
        # Core employer tools
        JobPostingTool(),  # Older tool - consider deprecating
        JobListingTool(),  # NEW - List/fetch existing job postings
        RecentHiresTool(),  # NEW - Query recent hires across all jobs
        ApplicationReviewTool(),  # NEW - Review applications and auto-update status
        ApplicationComparisonTool(),  # NEW - Compare candidates side-by-side
        ApplicationStatusTool(),  # NEW - Track application status
        JobDescriptionEnhancer(),
        MatchingTool(),  # Enhanced with restaurant scoring
        HybridProfileAnalyzer(),  # HYBRID - Fast profile analysis (3-5x faster)
        InterviewSchedulerTool(),  # Enhanced with reschedule, cancel, feedback
        OnboardingTool(),
        NotificationTool(),
        
        # Restaurant-specific helpers (usually called by BulkHiringWorkflow)
        PositionParserTool(),
        SLMPositionParser(),  # SLM - Fast position parsing
        BulkProfileProcessorTool(),
        QuantityBasedSelectorTool()
    ]

def get_employee_tools():
    """Get tools specific to employees."""
    return [
        ResumeParserTool(),
        ResumeGeneratorTool(),  # NEW - AI-powered resume generation
        JobFinderTool(),
        JobApplicationTool(),  # NEW - Apply to jobs via chat
        MatchingTool(),  # Enhanced with restaurant criteria
        ApplicationStatusTool(),  # NEW - Check application status
        NotificationTool(),
        HybridProfileAnalyzer(),  # HYBRID - Fast profile analysis (3-5x faster)
        SLMSkillExtractor(),  # SLM - Fast skill extraction
        OfferAcceptanceTool()  # NEW - Accept/decline job offers via chat
    ]

def get_common_tools():
    """Get tools available to both roles."""
    return [
        NotificationTool(),
        EmbeddingGenerator()
    ]
