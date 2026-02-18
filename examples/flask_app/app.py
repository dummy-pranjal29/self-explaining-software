"""
Flask Example - SES Intelligence SDK

This example demonstrates using ses-intelligence with Flask.

Usage:
    pip install ses-intelligence[flask]
    python app.py
"""

from flask import Flask, request, jsonify
from ses_intelligence import initialize, trace_behavior, get_runtime_snapshots
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.forecasting import ArchitectureHealthForecaster

# Initialize SES with your project ID
initialize(
    project_id="flask-app",
    enable_forecasting=True,
)

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "SES Intelligence Flask Example", "status": "ok"})


@trace_behavior
def process_user_data(user_id: int, action: str):
    """Process user data with tracing."""
    validate_input(user_id, action)
    result = execute_action(user_id, action)
    return result


@trace_behavior
def validate_input(user_id: int, action: str):
    """Validate request input."""
    if user_id <= 0:
        raise ValueError("Invalid user_id")
    return True


@trace_behavior
def execute_action(user_id: int, action: str):
    """Execute the requested action."""
    return {"user_id": user_id, "action": action, "status": "success"}


@app.route("/api/users/<int:user_id>", methods=["GET", "POST"])
def user_endpoint(user_id: int):
    """User API endpoint."""
    action = request.method.lower()
    result = process_user_data(user_id, action)
    return jsonify(result)


@app.route("/health")
def health_check():
    """Health check endpoint."""
    snapshots = get_runtime_snapshots()
    
    health_data = {
        "status": "ok",
        "snapshots": len(snapshots),
    }
    
    if snapshots:
        # Compute health
        health_engine = ArchitectureHealthEngine()
        health = health_engine.compute()
        health_data["health_score"] = health.get("overall_score", 0)
        
        # Forecast
        forecast_engine = ArchitectureHealthForecaster()
        forecast = forecast_engine.forecast(steps_ahead=3)
        health_data["forecast_direction"] = forecast.get("direction", "unknown")
    
    return jsonify(health_data)


@app.route("/stats")
def stats():
    """Get architecture statistics."""
    snapshots = get_runtime_snapshots()
    
    if not snapshots:
        return jsonify({"message": "No data available"})
    
    latest = snapshots[-1]
    return jsonify({
        "nodes": latest.graph.number_of_nodes(),
        "edges": latest.graph.number_of_edges(),
        "snapshot_id": latest.snapshot_id,
    })


if __name__ == "__main__":
    print("=" * 50)
    print("SES Intelligence - Flask Example")
    print("=" * 50)
    print("\nStarting Flask server on http://localhost:5000")
    print("\nTest endpoints:")
    print("  - http://localhost:5000/")
    print("  - http://localhost:5000/api/users/1")
    print("  - http://localhost:5000/health")
    print("  - http://localhost:5000/stats")
    print("\nPress Ctrl+C to stop")
    print("=" * 50)
    
    app.run(debug=True, port=5000)
