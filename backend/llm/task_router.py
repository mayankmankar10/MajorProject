"""
Task router for intelligent SLM vs GPT-4 selection.
Routes tasks to the most appropriate model based on complexity and requirements.
"""
import logging
from typing import Literal

logger = logging.getLogger(__name__)

TaskType = Literal[
    # SLM tasks (fast, simple)
    "extract_skills",
    "classify_job",
    "parse_positions",
    "filter_candidates",
    "extract_requirements",
    "categorize_experience",
    "parse_resume",
    
    # GPT-4 tasks (complex, accurate)
    "recommend_jobs",
    "rank_candidates",
    "generate_summary",
    "conversational_response",
    "final_selection",
    "personalized_advice",
    "complex_reasoning",
    
    # Hybrid tasks (both)
    "profile_analysis",
    "bulk_hiring",
    "job_matching"
]

class TaskRouter:
    """
    Routes tasks to appropriate LLM based on complexity.
    
    Routing Strategy:
    - SLM: Fast, simple, structured extraction tasks
    - GPT-4: Complex reasoning, recommendations, conversations
    - Hybrid: Use both (SLM filters, GPT-4 refines)
    """
    
    # Tasks suitable for SLM (fast, simple, structured)
    SLM_TASKS = {
        "extract_skills",
        "classify_job",
        "parse_positions",
        "filter_candidates",
        "extract_requirements",
        "categorize_experience",
        "parse_resume"
    }
    
    # Tasks requiring GPT-4 (complex, nuanced, conversational)
    GPT4_TASKS = {
        "recommend_jobs",
        "rank_candidates",
        "generate_summary",
        "conversational_response",
        "final_selection",
        "personalized_advice",
        "complex_reasoning"
    }
    
    # Tasks using hybrid approach (SLM + GPT-4)
    HYBRID_TASKS = {
        "profile_analysis",    # SLM extracts, GPT-4 summarizes
        "bulk_hiring",         # SLM screens, GPT-4 selects
        "job_matching"         # SLM filters, GPT-4 ranks
    }
    
    @staticmethod
    def should_use_slm(task_type: str) -> bool:
        """
        Determine if task should use SLM.
        
        Args:
            task_type: Type of task
            
        Returns:
            True if SLM should be used, False for GPT-4
        """
        return task_type in TaskRouter.SLM_TASKS
    
    @staticmethod
    def should_use_gpt4(task_type: str) -> bool:
        """
        Determine if task should use GPT-4.
        
        Args:
            task_type: Type of task
            
        Returns:
            True if GPT-4 should be used
        """
        return task_type in TaskRouter.GPT4_TASKS
    
    @staticmethod
    def is_hybrid_task(task_type: str) -> bool:
        """
        Determine if task should use hybrid approach.
        
        Args:
            task_type: Type of task
            
        Returns:
            True if both SLM and GPT-4 should be used
        """
        return task_type in TaskRouter.HYBRID_TASKS
    
    @staticmethod
    def get_routing_strategy(task_type: str) -> str:
        """
        Get routing strategy for task.
        
        Args:
            task_type: Type of task
            
        Returns:
            "slm", "gpt4", or "hybrid"
        """
        if task_type in TaskRouter.SLM_TASKS:
            return "slm"
        elif task_type in TaskRouter.GPT4_TASKS:
            return "gpt4"
        elif task_type in TaskRouter.HYBRID_TASKS:
            return "hybrid"
        else:
            # Default to GPT-4 for unknown tasks
            logger.warning(f"Unknown task type '{task_type}', defaulting to GPT-4")
            return "gpt4"
    
    @staticmethod
    def log_routing_decision(task_type: str, strategy: str):
        """Log routing decision for monitoring."""
        logger.info(f"🔀 Task '{task_type}' → {strategy.upper()}")


# Convenience function
def should_use_slm(task_type: str) -> bool:
    """Convenience function for SLM routing check."""
    return TaskRouter.should_use_slm(task_type)
