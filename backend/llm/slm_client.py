"""
SLM (Small Language Model) client using Google Gemini (new google.genai package).
Provides fast, cost-effective inference using Gemini Flash models.
"""
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

class SLMClient:
    """
    Client for Small Language Model using Google Gemini.
    
    Features:
    - Ultra-fast responses (0.3-0.5s)
    - Cost-effective (75% cheaper than GPT-4o-mini)
    - High quality (Google's latest models)
    - No self-hosting needed
    """
    
    def __init__(self):
        """Initialize SLM client with Gemini."""
        self.enabled = False
        self.client = None
        self.model_name = None
        
        # Check if SLM is enabled
        slm_enabled = os.getenv("SLM_ENABLED", "true").lower() == "true"
        
        if not slm_enabled:
            logger.info("📦 SLM disabled in configuration (SLM_ENABLED=false)")
            return
        
        try:
            # Import new Gemini client
            from google import genai
            
            # Get configuration
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("⚠️  GEMINI_API_KEY not found, falling back to GPT-4o-mini")
                self._init_openai_fallback()
                return
            
            # Initialize client
            self.client = genai.Client(api_key=api_key)
            
            # Use Gemini 2.0 Flash (latest, fastest, cheapest)
            self.model_name = os.getenv("SLM_MODEL", "gemini-2.0-flash-exp")
            
            # Test connection
            try:
                test_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents="test"
                )
                
                if test_response and test_response.text:
                    self.enabled = True
                    logger.info(f"✅ SLM connected: {self.model_name} (Gemini)")
                else:
                    logger.warning("⚠️  Gemini test failed, using GPT-4o-mini fallback")
                    self._init_openai_fallback()
            except Exception as test_error:
                logger.warning(f"⚠️  Gemini test failed: {test_error}")
                logger.info("💡 Falling back to GPT-4o-mini")
                self._init_openai_fallback()
                
        except ImportError:
            logger.warning("⚠️  google-genai not installed. Run: pip install google-genai")
            self._init_openai_fallback()
        except Exception as e:
            logger.warning(f"⚠️  Gemini unavailable: {e}")
            self._init_openai_fallback()
    
    def _init_openai_fallback(self):
        """Initialize OpenAI as fallback."""
        try:
            from langchain_openai import ChatOpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("❌ No OPENAI_API_KEY found for fallback")
                self.enabled = False
                return
            
            self.model_name = "gpt-4o-mini"
            self.client = ChatOpenAI(
                model=self.model_name,
                temperature=0.1,
                api_key=api_key
            )
            self.enabled = True
            logger.info(f"✅ SLM using fallback: {self.model_name} (OpenAI)")
            
        except Exception as e:
            logger.error(f"❌ Fallback initialization failed: {e}")
            self.enabled = False
    
    def invoke(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """
        Invoke SLM with prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if SLM unavailable
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Check if using Gemini or OpenAI
            if hasattr(self.client, 'models'):
                # New Gemini client
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={'max_output_tokens': max_tokens, 'temperature': 0.1}
                )
                return response.text
            else:
                # OpenAI fallback
                response = self.client.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                return content
            
        except Exception as e:
            logger.error(f"❌ SLM invocation error: {e}")
            return None
    
    def batch_invoke(self, prompts: list[str]) -> list[Optional[str]]:
        """
        Invoke SLM with multiple prompts.
        
        Args:
            prompts: List of prompts
            
        Returns:
            List of generated texts
        """
        if not self.enabled or not self.client:
            return [None] * len(prompts)
        
        results = []
        for prompt in prompts:
            result = self.invoke(prompt)
            results.append(result)
        
        return results
    
    def is_available(self) -> bool:
        """Check if SLM is available."""
        return self.enabled and self.client is not None


# Global SLM instance
_slm_client: Optional[SLMClient] = None

def get_slm_client() -> SLMClient:
    """Get or create global SLM client instance."""
    global _slm_client
    if _slm_client is None:
        _slm_client = SLMClient()
    return _slm_client
