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
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            api_key: API key for LLM provider (defaults to env var or Django settings)
            base_url: Base URL for LLM API (for LM Studio or other compatible APIs)
        """
        if api_key:
            self.api_key = api_key
        else:
            # First try Django settings (most reliable when running in Django)
            try:
                from django.conf import settings
                self.api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
            except ImportError:
                # Fall back to environment variable if Django not available
                self.api_key = os.environ.get('OPENAI_API_KEY')
        
        # Default to LM Studio if available, otherwise OpenAI
        if base_url:
            self.base_url = base_url
        else:
            # Check for LM Studio first, then fall back to OpenAI
            lm_studio_url = os.environ.get('LM_STUDIO_URL', 'http://localhost:1234/v1')
            self.base_url = lm_studio_url
        
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        """Check if LLM service is properly configured."""
        # LM Studio doesn't require an API key
        return True
    
    def _get_client(self):
        """Get or create LLM client."""
        if self._client is None:
            # Lazy import to avoid hard dependency
            try:
                from openai import OpenAI
                # LM Studio uses "not-needed" as placeholder API key
                api_key = self.api_key if self.api_key else "not-needed"
                self._client = OpenAI(api_key=api_key, base_url=self.base_url)
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
            
            # Use model from env or default to phi-3.1-mini-4k-instruct for LM Studio
            # Based on your available models: phi-3.1-mini-4k-instruct
            model_name = os.environ.get('LLM_MODEL', 'phi-3.1-mini-4k-instruct')
            
            response = client.chat.completions.create(
                model=model_name,
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
            # Provide a fallback response based on available data
            fallback_response = self._generate_fallback_response(
                health_data=health_data,
                forecast_data=forecast_data,
                historical_scores=historical_scores,
                recommendations=recommendations,
                question=question,
            )
            return {
                "status": "fallback",
                "message": f"OpenAI API unavailable: {str(e)}. Using local analysis.",
                "response": fallback_response,
            }
    
    def _generate_fallback_response(
        self,
        health_data: Dict[str, Any],
        forecast_data: Dict[str, Any],
        historical_scores: List[float],
        recommendations: List[str],
        question: str,
    ) -> str:
        """Generate a response from available data when LLM is unavailable."""
        question_lower = question.lower()
        
        # Extract health score
        health_score = health_data.get('health_score', 0)
        if health_score is None:
            health_score = 0
        
        # Determine health status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "moderately healthy"
        elif health_score >= 40:
            status = "degrading"
        else:
            status = "critical"
        
        # Analyze trend from historical scores
        trend = "stable"
        if len(historical_scores) >= 2:
            if historical_scores[-1] > historical_scores[0]:
                trend = "improving"
            elif historical_scores[-1] < historical_scores[0]:
                trend = "declining"
        
        # Build response based on question type
        if "health" in question_lower or "score" in question_lower:
            return f"Current architecture health score is {health_score:.1f}/100 ({status}). The trend is {trend} based on recent measurements."
        
        elif "risk" in question_lower or "problem" in question_lower:
            risk_indicators = health_data.get('risk_indicators', [])
            if risk_indicators:
                return f"Found {len(risk_indicators)} risk indicators. " + ". ".join(str(r) for r in risk_indicators[:3])
            return "No significant risks detected at this time."
        
        elif "forecast" in question_lower or "predict" in question_lower or "future" in question_lower:
            forecast_status = forecast_data.get('status', 'unknown')
            forecast_next = forecast_data.get('forecast_next')
            if forecast_next:
                return f"Forecast predicts a health score of approximately {forecast_next:.1f}. The forecast status is: {forecast_status}."
            return f"Forecast status: {forecast_status}. Not enough data for detailed prediction."
        
        elif "trend" in question_lower:
            if historical_scores:
                return f"Based on {len(historical_scores)} historical data points, the trend is {trend}. Recent scores: {', '.join(f'{s:.1f}' for s in historical_scores[-5:])}"
            return "Not enough historical data to determine trend."
        
        elif "recommend" in question_lower or "suggest" in question_lower:
            if recommendations:
                return "Recommendations: " + "; ".join(str(r) for r in recommendations[:3])
            return "No specific recommendations at this time. The system appears to be operating normally."
        
        else:
            # Default response with available info
            return f"Architecture Health: {health_score:.1f}/100 ({status}). Trend: {trend}. Forecast status: {forecast_data.get('status', 'unknown')}. Ask me about health, risks, forecasts, or recommendations."
    
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
