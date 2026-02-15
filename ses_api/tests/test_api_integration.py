"""
API Integration Tests.

Tests:
- /api/v1/health endpoint
- /api/v1/forecast endpoint
- Project create/delete endpoints
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ses_core.settings')

import django
django.setup()

from django.test import TestCase, Client
from ses_intelligence.project_storage import ProjectStorage


@pytest.mark.django_db
class TestHealthAPI(TestCase):
    """Test cases for /api/v1/health endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200 status."""
        response = self.client.get('/api/v1/health/')
        
        assert response.status_code == 200
    
    def test_health_endpoint_returns_json(self):
        """Test health endpoint returns JSON."""
        response = self.client.get('/api/v1/health/')
        
        assert response['Content-Type'].startswith('application/json')
    
    def test_health_endpoint_contains_project_id(self):
        """Test health response contains project_id."""
        response = self.client.get('/api/v1/health/')
        
        data = response.json()
        assert 'project_id' in data
    
    def test_health_endpoint_contains_timestamp(self):
        """Test health response contains timestamp."""
        response = self.client.get('/api/v1/health/')
        
        data = response.json()
        assert 'timestamp' in data
    
    def test_health_endpoint_with_custom_project(self):
        """Test health endpoint with custom project."""
        response = self.client.get('/api/v1/health/?project=test-project')
        
        assert response.status_code == 200
        data = response.json()
        assert data['project_id'] == 'test-project'


@pytest.mark.django_db
class TestForecastAPI(TestCase):
    """Test cases for /api/v1/forecast endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_forecast_endpoint_returns_200(self):
        """Test forecast endpoint returns 200 status."""
        response = self.client.get('/api/v1/forecast/')
        
        assert response.status_code == 200
    
    def test_forecast_endpoint_returns_json(self):
        """Test forecast endpoint returns JSON."""
        response = self.client.get('/api/v1/forecast/')
        
        assert response['Content-Type'].startswith('application/json')
    
    def test_forecast_endpoint_contains_forecast_key(self):
        """Test forecast response contains forecast key."""
        response = self.client.get('/api/v1/forecast/')
        
        data = response.json()
        assert 'forecast' in data
    
    def test_forecast_endpoint_contains_history_key(self):
        """Test forecast response contains history key."""
        response = self.client.get('/api/v1/forecast/')
        
        data = response.json()
        assert 'history' in data
    
    def test_forecast_endpoint_with_custom_project(self):
        """Test forecast endpoint with custom project."""
        response = self.client.get('/api/v1/forecast/?project=forecast-test')
        
        assert response.status_code == 200
        data = response.json()
        assert data['project_id'] == 'forecast-test'


@pytest.mark.django_db
class TestProjectAPI(TestCase):
    """Test cases for project management endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_projects_list_endpoint_returns_200(self):
        """Test projects list endpoint returns 200."""
        response = self.client.get('/api/v1/projects/')
        
        assert response.status_code == 200
    
    def test_projects_list_returns_json(self):
        """Test projects list returns JSON."""
        response = self.client.get('/api/v1/projects/')
        
        data = response.json()
        assert 'projects' in data
        assert isinstance(data['projects'], list)
    
    def test_project_create_endpoint(self):
        """Test project creation endpoint."""
        response = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'Test Project'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert 'project_id' in data
        assert data['status'] == 'created'
    
    def test_project_create_with_custom_id(self):
        """Test project creation with custom ID."""
        response = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'Custom ID Project', 'id': 'my-custom-id'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert 'project_id' in data
    
    def test_project_delete_endpoint(self):
        """Test project deletion endpoint."""
        # First create a project
        create_response = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'To Delete'}),
            content_type='application/json'
        )
        
        project_id = create_response.json()['project_id']
        
        # Now delete it
        delete_response = self.client.delete(f'/api/v1/projects/{project_id}/delete/')
        
        assert delete_response.status_code == 200
        
        data = delete_response.json()
        assert data['status'] == 'deleted'
    
    def test_project_delete_nonexistent(self):
        """Test deleting non-existent project."""
        response = self.client.delete('/api/v1/projects/nonexistent-id/delete/')
        
        # Should return not found
        data = response.json()
        assert data['status'] == 'not_found'
    
    def test_project_delete_default_not_allowed(self):
        """Test that default project cannot be deleted."""
        response = self.client.delete('/api/v1/projects/default/delete/')
        
        assert response.status_code == 400
        
        data = response.json()
        assert 'error' in data


@pytest.mark.django_db
class TestAPIValidation(TestCase):
    """Test API input validation."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_invalid_project_id_format(self):
        """Test invalid project ID format is handled."""
        # This should either reject or fallback to default
        response = self.client.get('/api/v1/health/?project=invalid@project!id')
        
        # Should either return 400 or fallback gracefully
        assert response.status_code in [200, 400]
    
    def test_project_id_length_validation(self):
        """Test project ID length validation."""
        # Long project ID should be handled
        long_id = 'a' * 100
        response = self.client.get(f'/api/v1/health/?project={long_id}')
        
        # Should handle gracefully
        assert response.status_code in [200, 400]


class TestAPIResponseFormat(TestCase):
    """Test API response format consistency."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_health_response_structure(self):
        """Test health response has expected structure."""
        response = self.client.get('/api/v1/health/')
        
        data = response.json()
        
        # Should have these keys
        assert 'timestamp' in data
        assert 'project_id' in data
    
    def test_forecast_response_structure(self):
        """Test forecast response has expected structure."""
        response = self.client.get('/api/v1/forecast/')
        
        data = response.json()
        
        # Should have these keys
        assert 'timestamp' in data
        assert 'project_id' in data
        assert 'history' in data
        assert 'forecast' in data


@pytest.mark.django_db
class TestProjectIsolation(TestCase):
    """Test project isolation in API."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_projects_are_isolated(self):
        """Test that different projects have isolated data."""
        # Create two projects
        proj1 = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'Project 1'}),
            content_type='application/json'
        ).json()['project_id']
        
        proj2 = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'Project 2'}),
            content_type='application/json'
        ).json()['project_id']
        
        # Get health for each project
        health1 = self.client.get(f'/api/v1/health/?project={proj1}').json()
        health2 = self.client.get(f'/api/v1/health/?project={proj2}').json()
        
        # Both should work independently
        assert health1['project_id'] == proj1
        assert health2['project_id'] == proj2
    
    def test_forecast_isolated_per_project(self):
        """Test forecast is isolated per project."""
        proj1 = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'Forecast Project 1'}),
            content_type='application/json'
        ).json()['project_id']
        
        proj2 = self.client.post(
            '/api/v1/projects/create/',
            data=json.dumps({'name': 'Forecast Project 2'}),
            content_type='application/json'
        ).json()['project_id']
        
        # Get forecast for each project
        forecast1 = self.client.get(f'/api/v1/forecast/?project={proj1}').json()
        forecast2 = self.client.get(f'/api/v1/forecast/?project={proj2}').json()
        
        # Both should work independently
        assert forecast1['project_id'] == proj1
        assert forecast2['project_id'] == proj2
