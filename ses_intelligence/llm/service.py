"""
LLM Service for conversational intelligence.

This service provides the LLM-powered chat capability.
"""

import os
import logging
from typing import Optional, Dict, Any, List

from .prompts import SYSTEM_PROMPT, build_context

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for LLM-powered conversational intelligence.
    
    This service:
    - Collects architecture health data
    - Builds context from metrics
    - Generates natural language explanations
    - Follows strict "LLM explains, LLM doesn't compute" rule
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            api_key: API key for LLM provider (defaults to env var or Django settings)
        """
        if api_key:
            self.api_key = api_key
        else:
            # Framework-agnostic: prefer env var, optionally try Django if available
            self.api_key = os.environ.get('OPENAI_API_KEY')
            
            # Optional: Try Django settings if Django is available and env var not set
            if not self.api_key:
                try:
                    from django.conf import settings
                    self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
                except ImportError:
                    pass
        
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        """Check if LLM service is properly configured."""
        return bool(self.api_key)
    
    def _get_client(self):
        """Get or create LLM client."""
        if not self.is_configured:
            raise ValueError(
                "LLM service not configured. "
                "Set OPENAI_API_KEY environment variable or provide api_key."
            )
        
        if self._client is None:
            # Lazy import to avoid hard dependency
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package required for LLM service. "
                    "Install with: pip install openai"
                )
        
        return self._client
    
    def get_response(
        self,
        project_id: str,
        project_name: str,
        health_data: Dict[str, Any],
        forecast_data: Dict[str, Any],
        historical_scores: List[float],
        recommendations: List[str],
        question: str,
    ) -> Dict[str, Any]:
        """
        Get LLM response to a question about project intelligence.
        
        Args:
            project_id: Project identifier
            project_name: Human-readable project name
            health_data: Current health metrics from engine
            forecast_data: Forecast results
            historical_scores: Historical health scores
            recommendations: List of recommendations
            question: User's question
            
        Returns:
            Dict containing response and metadata
        """
        if not self.is_configured:
            return {
                "status": "error",
                "message": "LLM service not configured. Set OPENAI_API_KEY.",
                "response": None,
            }
        
        try:
            # Build context from data
            context = build_context(
                project_name=project_name,
                project_id=project_id,
                health_data=health_data,
                forecast_data=forecast_data,
                historical_scores=historical_scores,
                recommendations=recommendations,
                question=question,
            )
            
            # Get LLM response
            client = self._get_client()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            }
            
        except Exception as e:
            logger.exception(f"LLM service error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "response": None,
            }
    
    def generate_summary(
        self,
        project_id: str,
        project_name: str,
        health_data: Dict[str, Any],
        forecast_data: Dict[str, Any],
    ) -> str:
        """
        Generate an executive summary using LLM.
        
        Args:
            project_id: Project identifier
            project_name: Human-readable project name
            health_data: Current health metrics
            forecast_data: Forecast results
            
        Returns:
            Natural language summary
        """
        result = self.get_response(
            project_id=project_id,
            project_name=project_name,
            health_data=health_data,
            forecast_data=forecast_data,
            historical_scores=[],
            recommendations=health_data.get('recommendations', []),
            question="Provide a brief executive summary of the architecture health and forecast.",
        )
        
        if result["status"] == "success":
            return result["response"]
        
        return "Executive summary unavailable. LLM service not configured."


# Default service instance
_default_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the default LLM service instance."""
    global _default_service
    if _default_service is None:
        _default_service = LLMService()
    return _default_service


def set_llm_service(service: LLMService) -> None:
    """Set the default LLM service instance."""
    global _default_service
    _default_service = service
