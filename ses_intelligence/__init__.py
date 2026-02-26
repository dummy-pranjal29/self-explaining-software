"""
Self-Evolving Software Intelligence (ses_intelligence)

A runtime intelligence platform that monitors, analyzes, and explains
software behavior changes in real-time.

Quick Start:
    from ses_intelligence import trace_behavior, initialize
    
    # Initialize with optional configuration
    initialize(
        project_id="my-project",
        enable_forecasting=True,
    )
    
    # Instrument your functions
    @trace_behavior
    def my_function():
        pass

For more details, see the documentation.
"""

__version__ = "1.0.0b3"

# Public API exports
from .tracing import trace_behavior, get_edge_features
from .runtime_state import get_runtime_snapshots, reset_runtime_state
from .project_storage import ProjectStorage, get_project_storage
from .config import (
    initialize,
    get_config,
    reset_config,
    is_initialized,
    is_forecasting_enabled,
    is_narratives_enabled,
    is_llm_enabled,
)
from .llm import LLMService, get_llm_service


def cli_main():
    """CLI entry point - imported lazily to avoid circular imports."""
    from .cli import main
    return main()


__all__ = [
    # Version
    "__version__",
    # CLI
    "cli_main",
    # Configuration
    "initialize",
    "get_config",
    "reset_config",
    "is_initialized",
    "is_forecasting_enabled",
    "is_narratives_enabled",
    "is_llm_enabled",
    # Tracing
    "trace_behavior",
    "get_edge_features",
    # Runtime State
    "get_runtime_snapshots",
    "reset_runtime_state",
    # Project Storage
    "ProjectStorage",
    "get_project_storage",
    # LLM Service
    "LLMService",
    "get_llm_service",
]
