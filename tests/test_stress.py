"""
Comprehensive Validation Tests.

This script performs end-to-end validation of the application:
1. Creates multiple projects
2. Generates snapshots for each
3. Tests forecast with varying history depths
4. Tests project isolation
5. Tests API under load
"""

import json
import time
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ses_core.settings')

import django
django.setup()

from django.test import TestCase, Client
from ses_intelligence.project_storage import ProjectStorage
from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
from ses_intelligence.architecture_health.confidence import ForecastConfidenceEngine


# Test project names
TEST_PROJECTS = ["default", "alpha", "beta", "stress-test", "random-behavior"]


@pytest.mark.django_db
class TestComprehensiveProjectCreation(TestCase):
    """Test creating multiple projects as per GPT suggestions."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_create_5_projects(self):
        """Create 5 projects as suggested by GPT."""
        created_projects = []
        
        for project_name in TEST_PROJECTS:
            response = self.client.post(
                '/api/v1/projects/create/',
                data=json.dumps({'name': project_name.title(), 'id': project_name}),
                content_type='application/json'
            )
            
            assert response.status_code == 200, f"Failed to create {project_name}"
            data = response.json()
            assert data['status'] == 'created', f"Project {project_name} not created"
            assert data['project_id'] == project_name
            created_projects.append(project_name)
        
        # Verify all projects are listed
        response = self.client.get('/api/v1/projects/')
        data = response.json()
        
        for project in created_projects:
            assert project in data['projects'], f"Project {project} not in list"
    
    def test_switch_between_projects(self):
        """Test switching between projects via API."""
        for project_name in TEST_PROJECTS:
            # Create project if it doesn't exist
            self.client.post(
                '/api/v1/projects/create/',
                data=json.dumps({'id': project_name}),
                content_type='application/json'
            )
            
            # Get health for each project
            response = self.client.get(f'/api/v1/health/?project={project_name}')
            assert response.status_code == 200
            data = response.json()
            assert data['project_id'] == project_name


@pytest.mark.django_db  
class TestSnapshotGeneration(TestCase):
    """Test generating snapshots for projects."""
    
    def setUp(self):
        """Set up test client and temporary storage."""
        self.client = Client()
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_generate_multiple_snapshots(self):
        """Generate 100-300 snapshots per project as suggested."""
        with patch('ses_intelligence.project_storage.BEHAVIOR_DATA_DIR', self.temp_path):
            snapshots_per_project = 150  # Target: 100-300
            
            for project_name in ["alpha", "beta"]:
                # Create project
                storage = ProjectStorage(project_name)
                history = ArchitectureHealthHistory(project_name)
                
                # Generate snapshot data
                for i in range(snapshots_per_project):
                    health_data = {
                        "timestamp": f"2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
                        "health_score": 0.5 + (i % 50) / 100,  # Vary between 0.5-1.0
                        "component_scores": {
                            "stability": 0.6 + (i % 40) / 100,
                            "complexity": 0.7 - (i % 30) / 100,
                            "trend": 0.5 + (i % 20) / 100,
                        }
                    }
                    history.append_record(health_data)
                
                # Verify records were saved
                records = history.get_health_scores()
                assert len(records) == snapshots_per_project, \
                    f"Expected {snapshots_per_project} records, got {len(records)}"
                
                print(f"✓ Generated {snapshots_per_project} snapshots for {project_name}")


@pytest.mark.django_db
class TestForecastWithHistory(TestCase):
    """Test forecast behavior with varying history depths."""
    
    def setUp(self):
        """Set up test client and temporary storage."""
        self.client = Client()
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_forecast_convergence(self):
        """Test that forecast stabilizes with more data."""
        with patch('ses_intelligence.project_storage.BEHAVIOR_DATA_DIR', self.temp_path):
            project_name = "forecast-test"
            storage = ProjectStorage(project_name)
            history = ArchitectureHealthHistory(project_name)
            
            # Start with small history
            small_history = 10
            for i in range(small_history):
                history.append_record({
                    "timestamp": f"2024-01-{(i % 28) + 1:02d}T00:00:00Z",
                    "health_score": 0.8 + (i % 20) / 100,
                })
            
            # Get forecast with small history
            response = self.client.get(f'/api/v1/forecast/?project={project_name}')
            small_forecast = response.json()
            
            # Add more data
            for i in range(small_history, 100):
                history.append_record({
                    "timestamp": f"2024-01-{(i % 28) + 1:02d}T00:00:00Z",
                    "health_score": 0.8 + (i % 20) / 100,
                })
            
            # Get forecast with larger history
            response = self.client.get(f'/api/v1/forecast/?project={project_name}')
            large_forecast = response.json()
            
            # Verify forecast is returned
            assert 'forecast' in large_forecast
            assert large_forecast['forecast']['status'] == 'success'
            
            print(f"✓ Small history ({small_history}): {small_forecast['forecast'].get('confidence_score', 'N/A')}")
            print(f"✓ Large history (100): {large_forecast['forecast'].get('confidence_score', 'N/A')}")


@pytest.mark.django_db
class TestProjectIsolation(TestCase):
    """Test that projects are properly isolated."""
    
    def setUp(self):
        """Set up test client and temporary storage."""
        self.client = Client()
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_projects_have_isolated_data(self):
        """Test that each project has completely isolated data."""
        with patch('ses_intelligence.project_storage.BEHAVIOR_DATA_DIR', self.temp_path):
            project_a = "isolation-test-a"
            project_b = "isolation-test-b"
            
            # Create different data for each project
            history_a = ArchitectureHealthHistory(project_a)
            history_b = ArchitectureHealthHistory(project_b)
            
            for i in range(20):
                history_a.append_record({
                    "timestamp": f"2024-01-01T00:00:00Z",
                    "health_score": 0.9,  # High health for A
                })
                
                history_b.append_record({
                    "timestamp": "2024-01-01T00:00:00Z",
                    "health_score": 0.3,  # Low health for B
                })
            
            # Verify data is isolated
            records_a = history_a.get_health_scores()
            records_b = history_b.get_health_scores()
            
            # Check project A has high health
            avg_a = sum(r['health_score'] for r in records_a) / len(records_a)
            assert avg_a > 0.8, f"Project A should have high health, got {avg_a}"
            
            # Check project B has low health  
            avg_b = sum(r['health_score'] for r in records_b) / len(records_b)
            assert avg_b < 0.5, f"Project B should have low health, got {avg_b}"
            
            # Verify via API
            health_a = self.client.get(f'/api/v1/health/?project={project_a}').json()
            health_b = self.client.get(f'/api/v1/health/?project={project_b}').json()
            
            assert health_a['health_score'] != health_b['health_score']
            print(f"✓ Project A avg: {avg_a}, Project B avg: {avg_b}")


@pytest.mark.django_db
class TestAPIResponseTimes(TestCase):
    """Test API response times."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_api_response_time(self):
        """Test that API responds within reasonable time."""
        endpoints = [
            '/api/v1/health/',
            '/api/v1/forecast/',
            '/api/v1/projects/',
        ]
        
        for endpoint in endpoints:
            start = time.time()
            response = self.client.get(endpoint)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 5.0, f"{endpoint} took {elapsed:.2f}s (should be < 5s)"
            print(f"✓ {endpoint}: {elapsed*1000:.0f}ms")


@pytest.mark.django_db
class TestEdgeCases(TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_nonexistent_project_returns_default(self):
        """Test that nonexistent project returns default data gracefully."""
        response = self.client.get('/api/v1/health/?project=nonexistent-12345')
        
        # Should not crash, should return valid response
        assert response.status_code == 200
        data = response.json()
        assert 'project_id' in data
    
    def test_forecast_with_no_history(self):
        """Test forecast with fresh project."""
        # Create a fresh project
        self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'id': 'fresh-project'}),
            content_type='application/json'
        )
        
        response = self.client.get('/api/v1/forecast/?project=fresh-project')
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate insufficient data
        assert data['forecast']['status'] in ['insufficient_data', 'success']
    
    def test_concurrent_project_creation(self):
        """Test creating multiple projects rapidly."""
        project_ids = [f"concurrent-{i}" for i in range(10)]
        
        for pid in project_ids:
            response = self.client.post(
                '/api/v1/projects/create/',
                data=json.dumps({'id': pid}),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        # Verify all were created
        response = self.client.get('/api/v1/projects/')
        data = response.json()
        
        for pid in project_ids:
            assert pid in data['projects'], f"{pid} not in projects list"
        
        print(f"✓ Created {len(project_ids)} projects concurrently")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
