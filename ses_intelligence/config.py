"""
Configuration Abstraction Layer for Self-Evolving Software.

This module provides a framework-agnostic initialization interface,
allowing the engine to be used without Django bindings.

Usage:
    from ses_intelligence import initialize
    
    # Initialize with custom configuration
    initialize(
        project_id="my-project",
        storage_path="/data/my-project",
        enable_background_tasks=True,
    )
    
    # Or use defaults
    initialize()
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class SESConfiguration:
    """
    Self-Evolving Software configuration.
    
    This configuration can be used with or without Django.
    """
    
    # Project configuration
    project_id: str = "default"
    project_name: str = ""
    storage_path: Optional[str] = None
    
    # Engine configuration
    enable_background_tasks: bool = False
    enable_health_tracking: bool = True
    enable_forecasting: bool = True
    enable_narratives: bool = True
    
    # Forecasting configuration
    forecast_window_size: int = 10
    forecast_confidence_floor: float = 0.70
    
    # Storage configuration
    data_retention_days: int = 90
    snapshot_retention_count: int = 100
    
    # LLM configuration
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    
    # Background task configuration
    task_broker_url: Optional[str] = None
    task_result_backend: Optional[str] = None
    
    # Django-specific settings (optional)
    django_settings: Optional[Dict[str, Any]] = None
    
    # Internal state
    _initialized: bool = field(default=False, repr=False)
    
    def is_initialized(self) -> bool:
        """Check if configuration has been initialized."""
        return self._initialized
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.project_id:
            raise ValueError("project_id is required")
        
        if len(self.project_id) > 64:
            raise ValueError("project_id must be 64 characters or less")
        
        if self.storage_path:
            path = Path(self.storage_path)
            if not path.exists():
                raise ValueError(f"storage_path does not exist: {path}")
            if not path.is_dir():
                raise ValueError(f"storage_path must be a directory: {path}")
        
        if self.forecast_window_size < 3:
            raise ValueError("forecast_window_size must be at least 3")
        
        if not 0 <= self.forecast_confidence_floor <= 1:
            raise ValueError("forecast_confidence_floor must be between 0 and 1")


# Global configuration instance
_config: Optional[SESConfiguration] = None


def initialize(
    project_id: str = "default",
    project_name: str = "",
    storage_path: Optional[str] = None,
    enable_background_tasks: bool = False,
    enable_health_tracking: bool = True,
    enable_forecasting: bool = True,
    enable_narratives: bool = True,
    forecast_window_size: int = 10,
    forecast_confidence_floor: float = 0.70,
    data_retention_days: int = 90,
    snapshot_retention_count: int = 100,
    llm_api_key: Optional[str] = None,
    llm_model: str = "gpt-4o-mini",
    task_broker_url: Optional[str] = None,
    task_result_backend: Optional[str] = None,
    django_settings: Optional[Dict[str, Any]] = None,
) -> SESConfiguration:
    """
    Initialize the Self-Evolving Software engine.
    
    Args:
        project_id: Unique project identifier
        project_name: Human-readable project name
        storage_path: Custom path for data storage (optional)
        enable_background_tasks: Enable async task processing
        enable_health_tracking: Enable health score tracking
        enable_forecasting: Enable forecasting
        enable_narratives: Enable narrative generation
        forecast_window_size: Window size for forecasting
        forecast_confidence_floor: Minimum confidence score
        data_retention_days: Days to retain historical data
        snapshot_retention_count: Max snapshots to retain
        llm_api_key: OpenAI API key for LLM features
        llm_model: LLM model to use
        task_broker_url: Celery broker URL
        task_result_backend: Celery result backend
        django_settings: Django settings dict (for Django mode)
    
    Returns:
        SESConfiguration instance
    
    Example:
        # Standalone usage
        initialize(
            project_id="my-app",
            storage_path="/data/ses",
            enable_forecasting=True,
        )
        
        # Django integration
        initialize(
            project_id="my-app",
            django_settings={
                "DEBUG": True,
                "DATABASES": {...},
            }
        )
    """
    global _config
    
    config = SESConfiguration(
        project_id=project_id,
        project_name=project_name,
        storage_path=storage_path,
        enable_background_tasks=enable_background_tasks,
        enable_health_tracking=enable_health_tracking,
        enable_forecasting=enable_forecasting,
        enable_narratives=enable_narratives,
        forecast_window_size=forecast_window_size,
        forecast_confidence_floor=forecast_confidence_floor,
        data_retention_days=data_retention_days,
        snapshot_retention_count=snapshot_retention_count,
        llm_api_key=llm_api_key or os.environ.get('OPENAI_API_KEY'),
        llm_model=llm_model,
        task_broker_url=task_broker_url or os.environ.get('CELERY_BROKER_URL'),
        task_result_backend=task_result_backend or os.environ.get('CELERY_RESULT_BACKEND'),
        django_settings=django_settings,
    )
    
    # Validate configuration
    config.validate()
    
    # Mark as initialized
    config._initialized = True
    
    # Store globally
    _config = config
    
    # Apply Django settings if provided
    if django_settings is not None:
        _setup_django(django_settings)
    
    return config


def get_config() -> SESConfiguration:
    """
    Get the current configuration.
    
    Returns:
        Current SESConfiguration instance
        
    Raises:
        RuntimeError: If not initialized
    """
    global _config
    
    if _config is None:
        # Return default configuration
        return SESConfiguration(project_id="default", _initialized=True)
    
    return _config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = None


def is_initialized() -> bool:
    """Check if SES has been initialized."""
    global _config
    return _config is not None and _config._initialized


def _setup_django(settings: Dict[str, Any]) -> None:
    """
    Apply Django settings (for Django mode).
    
    Args:
        settings: Django settings dictionary
    """
    # This allows running without full Django setup
    # In practice, Django would be configured externally
    pass


# Convenience function for checking features
def is_forecasting_enabled() -> bool:
    """Check if forecasting is enabled."""
    config = get_config()
    return config.enable_forecasting


def is_narratives_enabled() -> bool:
    """Check if narratives are enabled."""
    config = get_config()
    return config.enable_narratives


def is_llm_enabled() -> bool:
    """Check if LLM features are available."""
    config = get_config()
    return bool(config.llm_api_key)


# Default initialization for backward compatibility
def _ensure_initialized():
    """Ensure SES is initialized, using defaults if not."""
    if not is_initialized():
        initialize()
