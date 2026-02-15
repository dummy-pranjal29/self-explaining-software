"""
LLM Service for conversational intelligence.

This module provides LLM-powered conversational capabilities for the
Self-Evolving Software platform.

IMPORTANT: LLM explains. LLM does NOT compute.
The LLM is used to generate natural language explanations grounded in
the mathematical outputs from the intelligence engine, not to perform
computations.
"""

from .service import LLMService, get_llm_service
from .prompts import SYSTEM_PROMPT

__all__ = ['LLMService', 'get_llm_service', 'SYSTEM_PROMPT']
