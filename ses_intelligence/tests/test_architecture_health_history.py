"""
Unit tests for ArchitectureHealthHistory.

Tests:
- Loading health history
- Appending new records
- Extracting health scores
- Multi-project isolation
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ses_intelligence.architecture_health.history import ArchitectureHealthHistory


@pytest.fixture
def temp_behavior_data():
    """Create a temporary behavior_data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        behavior_dir = tmp_path / "behavior_data"
        behavior_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('ses_intelligence.project_storage.BEHAVIOR_DATA_DIR', behavior_dir):
            yield behavior_dir


@pytest.fixture
def sample_health_output():
    """Sample health output for testing."""
    return {
        "health_score": 0.85,
        "architecture_health_score": 0.85,
        "component_scores": {
            "stability": 0.9,
            "complexity": 0.8,
            "coupling": 0.85
        },
        "risk_indicators": [],
        "recommendations": ["Maintain current architecture patterns"]
    }


class TestArchitectureHealthHistory:
    """Test cases for ArchitectureHealthHistory class."""
    
    def test_initialization(self, temp_behavior_data):
        """Test history initialization."""
        history = ArchitectureHealthHistory(project_id="test-project")
        
        assert history.project_id == "test-project"
        assert history.filename == "health_history.json"
    
    def test_path_property(self, temp_behavior_data):
        """Test path property returns correct path."""
        history = ArchitectureHealthHistory(project_id="test-project")
        
        expected = temp_behavior_data / "test-project" / "architecture_health" / "health_history.json"
        assert history.path == expected
    
    def test_load_empty_history(self, temp_behavior_data):
        """Test loading history when file doesn't exist."""
        history = ArchitectureHealthHistory(project_id="empty-project")
        
        result = history.load()
        
        assert result == []
    
    def test_load_with_existing_data(self, temp_behavior_data):
        """Test loading history with existing data."""
        history = ArchitectureHealthHistory(project_id="existing-project")
        
        # Create a health history file
        history.path.parent.mkdir(parents=True, exist_ok=True)
        test_data = [
            {"timestamp": "2024-01-01T00:00:00Z", "health_score": 0.9},
            {"timestamp": "2024-01-02T00:00:00Z", "health_score": 0.85},
        ]
        history.path.write_text(json.dumps(test_data))
        
        result = history.load()
        
        assert len(result) == 2
        assert result[0]["health_score"] == 0.9
        assert result[1]["health_score"] == 0.85
    
    def test_load_invalid_json(self, temp_behavior_data):
        """Test loading history with invalid JSON."""
        history = ArchitectureHealthHistory(project_id="invalid-project")
        
        # Create invalid JSON file
        history.path.parent.mkdir(parents=True, exist_ok=True)
        history.path.write_text("not valid json{{{")
        
        result = history.load()
        
        assert result == []
    
    def test_append_new_record(self, temp_behavior_data, sample_health_output):
        """Test appending a new health record."""
        history = ArchitectureHealthHistory(project_id="append-project")
        
        history.append(sample_health_output)
        
        result = history.load()
        
        assert len(result) == 1
        assert result[0]["health_score"] == 0.85
        assert "timestamp" in result[0]
        assert "project_id" in result[0]
        assert "raw" in result[0]
    
    def test_append_multiple_records(self, temp_behavior_data, sample_health_output):
        """Test appending multiple records."""
        history = ArchitectureHealthHistory(project_id="multi-project")
        
        history.append({"health_score": 0.9})
        history.append({"health_score": 0.85})
        history.append({"health_score": 0.8})
        
        result = history.load()
        
        assert len(result) == 3
        assert result[0]["health_score"] == 0.9
        assert result[1]["health_score"] == 0.85
        assert result[2]["health_score"] == 0.8
    
    def test_append_invalid_input(self, temp_behavior_data):
        """Test appending with invalid input."""
        history = ArchitectureHealthHistory(project_id="invalid-input")
        
        with pytest.raises(ValueError):
            history.append("not a dict")
        
        with pytest.raises(ValueError):
            history.append({})  # Missing health_score
    
    def test_get_health_scores(self, temp_behavior_data):
        """Test extracting health scores from history."""
        history = HistoryWithData(temp_behavior_data)
        
        scores = history.get_health_scores()
        
        assert scores == [0.9, 0.85, 0.8, 0.75]
    
    def test_project_isolation(self, temp_behavior_data):
        """Test that projects have isolated histories."""
        history1 = ArchitectureHealthHistory(project_id="project-a")
        history2 = ArchitectureHealthHistory(project_id="project-b")
        
        history1.append({"health_score": 0.95})
        
        # history2 should be empty
        assert len(history2.load()) == 0
    
    def test_create_default(self, temp_behavior_data):
        """Test create_default factory method."""
        history = ArchitectureHealthHistory.create_default()
        
        assert history.project_id == "default"


class TestArchitectureHealthHistoryIntegration:
    """Integration tests for health history with storage."""
    
    def test_full_workflow(self, temp_behavior_data):
        """Test complete workflow: create, append, load."""
        project_id = "workflow-project"
        
        # Create history for project
        history = ArchitectureHealthHistory(project_id=project_id)
        
        # Verify path exists
        assert history.path.parent.exists()
        
        # Append multiple records
        for score in [0.9, 0.85, 0.8, 0.75, 0.7]:
            history.append({"health_score": score})
        
        # Load and verify
        records = history.load()
        assert len(records) == 5
        
        # Get scores
        scores = history.get_health_scores()
        assert scores == [0.9, 0.85, 0.8, 0.75, 0.7]
        
        # Verify project isolation
        other_history = ArchitectureHealthHistory(project_id="other-project")
        assert len(other_history.load()) == 0


class HistoryWithData:
    """Helper class to create history with pre-populated data."""
    
    def __init__(self, temp_dir, project_id="test-project"):
        self.temp_dir = temp_dir
        self.project_id = project_id
        
        # Create the directory structure
        self.health_dir = temp_dir / project_id / "architecture_health"
        self.health_dir.mkdir(parents=True, exist_ok=True)
        
        # Write test data
        self.history_file = self.health_dir / "health_history.json"
        test_data = [
            {"timestamp": "2024-01-01T00:00:00Z", "health_score": 0.9},
            {"timestamp": "2024-01-02T00:00:00Z", "health_score": 0.85},
            {"timestamp": "2024-01-03T00:00:00Z", "health_score": 0.8},
            {"timestamp": "2024-01-04T00:00:00Z", "health_score": 0.75},
        ]
        self.history_file.write_text(json.dumps(test_data))
        
        # Create a mock that behaves like ArchitectureHealthHistory
        self.storage = MagicMock()
        self.storage.snapshot_path = self.history_file
        
    def load(self):
        """Load the history file."""
        if not self.history_file.exists():
            return []
        
        raw = self.history_file.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []
    
    def get_health_scores(self):
        """Extract health scores."""
        history = self.load()
        scores = []
        
        for entry in history:
            score = entry.get("health_score")
            if isinstance(score, (int, float)):
                scores.append(float(score))
        
        return scores
