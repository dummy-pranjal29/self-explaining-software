"""
ses_intelligence.project_storage

Multi-project storage abstraction layer.

Manages project-scoped directory structure:
behavior_data/
└── <project_id>/
    ├── snapshots/
    └── architecture_health/

This enables true multi-project isolation while maintaining
filesystem-based storage for performance.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional


# ------------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
BEHAVIOR_DATA_DIR = BASE_DIR / "behavior_data"


# ------------------------------------------------------------------
# PROJECT STORAGE MANAGER
# ------------------------------------------------------------------

class ProjectStorage:
    """
    Manages project-scoped storage directories.
    
    Provides:
    - Automatic project directory creation
    - Project-scoped paths for snapshots and health data
    - Default project support for backward compatibility
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize with project_id.
        
        Args:
            project_id: Unique project identifier. 
                       If None, uses 'default' for backward compatibility.
        """
        self.project_id = project_id or "default"
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create project directories if they don't exist."""
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.health_dir.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------
    # PATH PROPERTIES
    # -------------------------------------------------
    
    @property
    def project_dir(self) -> Path:
        """Project root directory."""
        return BEHAVIOR_DATA_DIR / self.project_id
    
    @property
    def snapshots_dir(self) -> Path:
        """Directory for behavior snapshots."""
        return self.project_dir / "snapshots"
    
    @property
    def health_dir(self) -> Path:
        """Directory for architecture health data."""
        return self.project_dir / "architecture_health"
    
    @property
    def snapshot_path(self) -> Path:
        """Path to health history JSON file."""
        return self.health_dir / "health_history.json"
    
    # -------------------------------------------------
    # PROJECT MANAGEMENT
    # -------------------------------------------------
    
    @staticmethod
    def list_projects() -> list[str]:
        """
        List all existing project IDs.
        
        Returns:
            List of project directory names.
        """
        if not BEHAVIOR_DATA_DIR.exists():
            return []
        
        projects = []
        for item in BEHAVIOR_DATA_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                projects.append(item.name)
        
        return sorted(projects)
    
    @staticmethod
    def create_project(project_id: Optional[str] = None) -> str:
        """
        Create a new project directory structure.
        
        Args:
            project_id: Optional custom project ID.
                       If None, generates a UUID.
        
        Returns:
            The created project_id.
        """
        if project_id is None:
            project_id = str(uuid.uuid4())[:8]
        
        storage = ProjectStorage(project_id)
        return project_id
    
    @staticmethod
    def delete_project(project_id: str) -> bool:
        """
        Delete a project and all its data.
        
        Args:
            project_id: Project to delete.
        
        Returns:
            True if deleted, False if not found.
        """
        project_dir = BEHAVIOR_DATA_DIR / project_id
        
        if not project_dir.exists():
            return False
        
        import shutil
        shutil.rmtree(project_dir)
        return True
    
    @staticmethod
    def project_exists(project_id: str) -> bool:
        """Check if a project exists."""
        return (BEHAVIOR_DATA_DIR / project_id).exists()


# ------------------------------------------------------------------
# DEFAULT PROJECT STORAGE (BACKWARD COMPATIBILITY)
# ------------------------------------------------------------------

def get_default_storage() -> ProjectStorage:
    """
    Get default project storage for backward compatibility.
    
    Returns:
        ProjectStorage instance for 'default' project.
    """
    return ProjectStorage("default")


def get_project_storage(project_id: Optional[str] = None) -> ProjectStorage:
    """
    Get project storage for a specific project.
    
    Args:
        project_id: Project identifier. Uses 'default' if None.
    
    Returns:
        ProjectStorage instance for the project.
    """
    return ProjectStorage(project_id)
