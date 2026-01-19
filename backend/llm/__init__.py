# backend/llm/__init__.py
"""
LLM clients for hybrid SLM + GPT-4 architecture.
Provides both local SLM (Ollama) and cloud LLM (OpenAI) with intelligent routing.
"""

from backend.llm.slm_client import SLMClient, get_slm_client
from backend.llm.task_router import TaskRouter, should_use_slm

__all__ = [
    'SLMClient',
    'get_slm_client',
    'TaskRouter',
    'should_use_slm'
]
