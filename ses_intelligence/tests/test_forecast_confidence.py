"""
Unit tests for ForecastConfidenceEngine.

Tests:
- Rolling regression
- RMSE calculation
- Confidence interval computation
- Volatility classification
- Confidence score calculation
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ses_intelligence.architecture_health.confidence import ForecastConfidenceEngine


@pytest.fixture
def sample_health_data():
    """Sample health history data for testing."""
    return [
        {"timestamp": "2024-01-01T00:00:00Z", "health_score": 0.9},
        {"timestamp": "2024-01-02T00:00:00Z", "health_score": 0.88},
        {"timestamp": "2024-01-03T00:00:00Z", "health_score": 0.85},
        {"timestamp": "2024-01-04T00:00:00Z", "health_score": 0.82},
        {"timestamp": "2024-01-05T00:00:00Z", "health_score": 0.80},
        {"timestamp": "2024-01-06T00:00:00Z", "health_score": 0.78},
        {"timestamp": "2024-01-07T00:00:00Z", "health_score": 0.75},
        {"timestamp": "2024-01-08T00:00:00Z", "health_score": 0.72},
        {"timestamp": "2024-01-09T00:00:00Z", "health_score": 0.70},
        {"timestamp": "2024-01-10T00:00:00Z", "health_score": 0.68},
        {"timestamp": "2024-01-11T00:00:00Z", "health_score": 0.65},
        {"timestamp": "2024-01-12T00:00:00Z", "health_score": 0.62},
    ]


@pytest.fixture
def temp_history_file(sample_health_data):
    """Create a temporary history file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_health_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


class TestForecastConfidenceEngine:
    """Test cases for ForecastConfidenceEngine class."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = ForecastConfidenceEngine(window_size=10)
        
        assert engine.window_size == 10
        assert engine.history_path is None
    
    def test_initialization_with_path(self, temp_history_file):
        """Test engine initialization with history path."""
        engine = ForecastConfidenceEngine(history_path=temp_history_file, window_size=5)
        
        assert engine.history_path == temp_history_file
        assert engine.window_size == 5
    
    def test_extract_health_values(self, sample_health_data):
        """Test health value extraction from history data."""
        engine = ForecastConfidenceEngine()
        
        values = engine._extract_health_values(sample_health_data)
        
        assert values == [0.9, 0.88, 0.85, 0.82, 0.80, 0.78, 0.75, 0.72, 0.70, 0.68, 0.65, 0.62]
    
    def test_extract_health_values_with_raw_field(self):
        """Test extraction from data with 'raw' field."""
        engine = ForecastConfidenceEngine()
        
        data = [
            {"timestamp": "2024-01-01T00:00:00Z", "raw": {"health_score": 0.85}},
            {"timestamp": "2024-01-02T00:00:00Z", "raw": {"health_score": 0.80}},
        ]
        
        values = engine._extract_health_values(data)
        
        assert values == [0.85, 0.80]
    
    def test_extract_health_values_with_alternative_key(self):
        """Test extraction with alternative health score key."""
        engine = ForecastConfidenceEngine()
        
        data = [
            {"timestamp": "2024-01-01T00:00:00Z", "architecture_health_score": 0.85},
        ]
        
        values = engine._extract_health_values(data)
        
        assert values == [0.85]
    
    def test_load_health_history(self, temp_history_file):
        """Test loading health history from file."""
        engine = ForecastConfidenceEngine(history_path=temp_history_file)
        
        values = engine.load_health_history()
        
        assert len(values) == 12
        assert values[0] == 0.9
    
    def test_load_health_history_nonexistent_file(self):
        """Test loading from non-existent file."""
        engine = ForecastConfidenceEngine(history_path="/nonexistent/file.json")
        
        values = engine.load_health_history()
        
        assert values == []
    
    def test_rolling_regression(self):
        """Test rolling regression calculation."""
        engine = ForecastConfidenceEngine(window_size=5)
        
        values = [0.9, 0.85, 0.80, 0.75, 0.70]
        predictions, residuals = engine.rolling_regression(values)
        
        assert len(predictions) == 5
        assert len(residuals) == 5
    
    def test_compute_rmse(self):
        """Test RMSE calculation."""
        import numpy as np
        engine = ForecastConfidenceEngine()
        
        residuals = np.array([0.1, -0.05, 0.02, -0.03, 0.01])
        rmse = engine.compute_rmse(residuals)
        
        expected_rmse = ((0.1**2 + 0.05**2 + 0.02**2 + 0.03**2 + 0.01**2) / 5) ** 0.5
        assert abs(rmse - expected_rmse) < 0.001
    
    def test_compute_variance(self):
        """Test variance calculation."""
        engine = ForecastConfidenceEngine()
        
        residuals = [0.1, -0.05, 0.02, -0.03, 0.01]
        variance = engine.compute_variance(residuals)
        
        expected_variance = 0.0028  # Approximate
        assert abs(variance - expected_variance) < 0.01
    
    def test_forecast_next(self):
        """Test next value forecasting."""
        engine = ForecastConfidenceEngine(window_size=5)
        
        values = [0.9, 0.85, 0.80, 0.75, 0.70]
        next_value = engine.forecast_next(values)
        
        # Next value should be a float
        assert isinstance(next_value, float)
        # Should be close to the trend
        assert next_value < 0.70  # Declining trend
    
    def test_compute_confidence_interval(self):
        """Test confidence interval calculation."""
        engine = ForecastConfidenceEngine()
        
        prediction = 0.65
        std_dev = 0.05
        
        lower, upper = engine.compute_confidence_interval(prediction, std_dev)
        
        # 95% confidence interval (z=1.96)
        assert lower < prediction
        assert upper > prediction
        assert upper - lower == pytest.approx(1.96 * 0.05 * 2)
    
    def test_compute_confidence_score(self):
        """Test confidence score calculation."""
        engine = ForecastConfidenceEngine()
        
        # Low RMSE relative to mean = high confidence
        score = engine.compute_confidence_score(rmse=0.02, mean_health=0.8)
        assert score > 0.9
        
        # High RMSE relative to mean = low confidence
        score = engine.compute_confidence_score(rmse=0.3, mean_health=0.5)
        assert score >= 0.70  # Minimum floor
    
    def test_compute_confidence_score_zero_mean(self):
        """Test confidence score with zero mean."""
        engine = ForecastConfidenceEngine()
        
        score = engine.compute_confidence_score(rmse=0.1, mean_health=0.0)
        
        assert score == 0.0
    
    def test_classify_volatility(self):
        """Test volatility classification."""
        engine = ForecastConfidenceEngine()
        
        assert engine.classify_volatility(0.02) == "low"
        assert engine.classify_volatility(0.10) == "moderate"
        assert engine.classify_volatility(0.30) == "high"
    
    def test_run_with_sufficient_data(self, temp_history_file):
        """Test running engine with sufficient data."""
        engine = ForecastConfidenceEngine(history_path=temp_history_file, window_size=10)
        
        result = engine.run()
        
        assert result["status"] == "success"
        assert "forecast_next" in result
        assert "confidence_interval" in result
        assert "rmse" in result
        assert "confidence_score" in result
        assert "volatility" in result
    
    def test_run_with_insufficient_data(self):
        """Test running engine with insufficient data."""
        engine = ForecastConfidenceEngine(window_size=10)
        
        # Less data than window_size
        values = [0.9, 0.85, 0.80]
        
        result = engine._compute(values)
        
        assert result["status"] == "insufficient_data"
    
    def test_run_from_memory(self, sample_health_data):
        """Test running engine from memory."""
        engine = ForecastConfidenceEngine(window_size=10)
        
        result = engine.run_from_memory(sample_health_data)
        
        assert result["status"] == "success"
        assert "forecast_next" in result
        assert "confidence_score" in result
    
    def test_confidence_score_minimum_floor(self):
        """Test that confidence score has minimum floor of 0.70."""
        engine = ForecastConfidenceEngine()
        
        # Very high RMSE should still return at least 0.70
        score = engine.compute_confidence_score(rmse=1.0, mean_health=0.5)
        
        assert score >= 0.70
    
    def test_trend_detection_declining(self, sample_health_data):
        """Test that declining trend is properly detected."""
        engine = ForecastConfidenceEngine(window_size=10)
        
        result = engine.run_from_memory(sample_health_data)
        
        # The health scores are declining, so forecast should be lower
        assert result["forecast_next"] < 0.62  # Last value
    
    def test_result_structure(self):
        """Test that result has expected structure."""
        engine = ForecastConfidenceEngine(window_size=5)
        
        values = [0.9, 0.88, 0.86, 0.84, 0.82]
        result = engine._compute(values)
        
        expected_keys = [
            "status",
            "forecast_next",
            "confidence_interval",
            "rmse",
            "residual_variance",
            "confidence_score",
            "volatility"
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert "lower" in result["confidence_interval"]
        assert "upper" in result["confidence_interval"]


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_values(self):
        """Test with empty values list."""
        engine = ForecastConfidenceEngine()
        
        result = engine._compute([])
        
        assert result["status"] == "insufficient_data"
    
    def test_single_value(self):
        """Test with single value."""
        engine = ForecastConfidenceEngine(window_size=10)
        
        result = engine._compute([0.9])
        
        assert result["status"] == "insufficient_data"
    
    def test_exactly_window_size_values(self):
        """Test with exactly window_size values."""
        engine = ForecastConfidenceEngine(window_size=5)
        
        values = [0.9, 0.85, 0.80, 0.75, 0.70]
        
        result = engine._compute(values)
        
        assert result["status"] == "success"
    
    def test_none_values_in_data(self):
        """Test handling of None values in data."""
        engine = ForecastConfidenceEngine()
        
        data = [
            {"timestamp": "2024-01-01T00:00:00Z", "health_score": 0.9},
            {"timestamp": "2024-01-02T00:00:00Z"},  # Missing health_score
            {"timestamp": "2024-01-03T00:00:00Z", "health_score": 0.85},
        ]
        
        values = engine._extract_health_values(data)
        
        assert values == [0.9, 0.85]
    
    def test_non_dict_entries(self):
        """Test handling of non-dict entries in data."""
        engine = ForecastConfidenceEngine()
        
        data = [
            {"timestamp": "2024-01-01T00:00:00Z", "health_score": 0.9},
            "not a dict",
            123,
            {"timestamp": "2024-01-02T00:00:00Z", "health_score": 0.85},
        ]
        
        values = engine._extract_health_values(data)
        
        assert values == [0.9, 0.85]
