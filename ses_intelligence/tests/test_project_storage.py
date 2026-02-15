"""
Unit tests for ProjectStorage.

Tests:
- Project creation and deletion
- Project listing
- Directory structure creation
- Project isolation
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ses_intelligence.project_storage import ProjectStorage


@pytest.fixture
def temp_behavior_data():
    """Create a temporary behavior_data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        behavior_dir = tmp_path / "behavior_data"
        behavior_dir.mkdir(parents=True, exist_ok=True)
        
        # Patch the BEHAVIOR_DATA_DIR
        with patch('ses_intelligence.project_storage.BEHAVIOR_DATA_DIR', behavior_dir):
            yield behavior_dir


class TestProjectStorage:
    """Test cases for ProjectStorage class."""
    
    def test_default_project_creation(self, temp_behavior_data):
        """Test creating a default project."""
        storage = ProjectStorage("test-project-1")
        
        assert storage.project_id == "test-project-1"
        assert storage.project_dir.exists()
        assert storage.snapshots_dir.exists()
        assert storage.health_dir.exists()
    
    def test_project_directory_structure(self, temp_behavior_data):
        """Test that project creates correct directory structure."""
        storage = ProjectStorage("test-project-2")
        
        expected_dirs = [
            storage.project_dir,
            storage.snapshots_dir,
            storage.health_dir,
        ]
        
        for d in expected_dirs:
            assert d.exists(), f"Expected directory {d} to exist"
            assert d.is_dir(), f"Expected {d} to be a directory"
    
    def test_snapshot_path_property(self, temp_behavior_data):
        """Test snapshot_path property returns correct path."""
        storage = ProjectStorage("test-project-3")
        
        expected_path = storage.health_dir / "health_history.json"
        assert storage.snapshot_path == expected_path
    
    def test_list_projects_empty(self, temp_behavior_data):
        """Test listing projects when none exist."""
        projects = ProjectStorage.list_projects()
        assert projects == []
    
    def test_list_projects_multiple(self, temp_behavior_data):
        """Test listing multiple projects."""
        # Create some projects
        ProjectStorage("project-a")
        ProjectStorage("project-b")
        ProjectStorage("project-c")
        
        projects = ProjectStorage.list_projects()
        
        assert len(projects) == 3
        assert "project-a" in projects
        assert "project-b" in projects
        assert "project-c" in projects
    
    def test_create_project_with_custom_id(self, temp_behavior_data):
        """Test creating project with custom ID."""
        project_id = ProjectStorage.create_project("my-custom-project")
        
        assert project_id == "my-custom-project"
        assert ProjectStorage.project_exists("my-custom-project")
    
    def test_create_project_with_auto_generated_id(self, temp_behavior_data):
        """Test creating project with auto-generated ID."""
        project_id = ProjectStorage.create_project()
        
        assert project_id is not None
        assert len(project_id) > 0
        assert ProjectStorage.project_exists(project_id)
    
    def test_delete_existing_project(self, temp_behavior_data):
        """Test deleting an existing project."""
        ProjectStorage("project-to-delete")
        
        assert ProjectStorage.project_exists("project-to-delete")
        
        result = ProjectStorage.delete_project("project-to-delete")
        
        assert result is True
        assert not ProjectStorage.project_exists("project-to-delete")
    
    def test_delete_nonexistent_project(self, temp_behavior_data):
        """Test deleting a non-existent project."""
        result = ProjectStorage.delete_project("nonexistent-project")
        
        assert result is False
    
    def test_project_exists(self, temp_behavior_data):
        """Test checking if project exists."""
        assert not ProjectStorage.project_exists("new-project")
        
        ProjectStorage("new-project")
        
        assert ProjectStorage.project_exists("new-project")
    
    def test_project_isolation(self, temp_behavior_data):
        """Test that projects are isolated from each other."""
        storage1 = ProjectStorage("project-1")
        storage2 = ProjectStorage("project-2")
        
        # Different projects should have different directories
        assert storage1.project_dir != storage2.project_dir
        assert storage1.snapshots_dir != storage2.snapshots_dir
        assert storage1.health_dir != storage2.health_dir
        
        # Write to one project should not affect the other
        test_file = storage1.snapshots_dir / "test.json"
        test_file.write_text('{"test": true}')
        
        assert not (storage2.snapshots_dir / "test.json").exists()


class TestBackwardCompatibility:
    """Test backward compatibility functions."""
    
    def test_get_default_storage(self, temp_behavior_data):
        """Test get_default_storage returns default project."""
        from ses_intelligence.project_storage import get_default_storage
        storage = get_default_storage()
        
        assert storage.project_id == "default"
        assert storage.project_dir.exists()
    
    def test_get_project_storage_with_none(self, temp_behavior_data):
        """Test get_project_storage with None returns default."""
        from ses_intelligence.project_storage import get_project_storage
        storage = get_project_storage(None)
        
        assert storage.project_id == "default"
    
    def test_get_project_storage_with_id(self, temp_behavior_data):
        """Test get_project_storage with custom ID."""
        from ses_intelligence.project_storage import get_project_storage
        storage = get_project_storage("custom-id")
        
        assert storage.project_id == "custom-id"
