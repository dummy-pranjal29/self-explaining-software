"""
Plain Python Example - SES Intelligence SDK

This example demonstrates using ses-intelligence in a plain Python script.
No web framework required - works in any Python application.

Usage:
    pip install ses-intelligence
    python example.py
"""

from ses_intelligence import initialize, trace_behavior, get_runtime_snapshots
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.forecasting import ArchitectureHealthForecaster
from ses_intelligence.ml.features import FeatureExtractor


# Initialize SES with your project ID
initialize(
    project_id="my-app",
    enable_forecasting=True,
)


# Instrument your functions with @trace_behavior
@trace_behavior
def save_user(user_data: dict):
    """Simulated user save operation."""
    # Your business logic here
    validate_user(user_data)
    store_in_database(user_data)
    send_welcome_email(user_data)
    return {"status": "success", "user_id": 123}


@trace_behavior
def validate_user(user_data: dict):
    """Validate user data."""
    # Simulated validation
    if not user_data.get("email"):
        raise ValueError("Email required")
    return True


@trace_behavior
def store_in_database(user_data: dict):
    """Simulated database storage."""
    # Simulated DB operation
    pass


@trace_behavior
def send_welcome_email(user_data: dict):
    """Simulated email sending."""
    # Simulated email
    pass


@trace_behavior
def get_user(user_id: int):
    """Simulated user retrieval."""
    fetch_from_database(user_id)
    enrich_user_data(user_id)
    return {"id": user_id, "name": "John Doe"}


@trace_behavior
def fetch_from_database(user_id: int):
    """Simulated DB fetch."""
    pass


@trace_behavior
def enrich_user_data(user_id: int):
    """Enrich user with additional data."""
    pass


def main():
    """Run the example."""
    print("=" * 50)
    print("SES Intelligence - Plain Python Example")
    print("=" * 50)
    
    # Simulate some application behavior
    print("\n1. Creating a new user...")
    result = save_user({"email": "john@example.com", "name": "John"})
    print(f"   Result: {result}")
    
    print("\n2. Retrieving user...")
    user = get_user(123)
    print(f"   Result: {user}")
    
    print("\n3. Creating another user...")
    save_user({"email": "jane@example.com", "name": "Jane"})
    
    # Get runtime snapshots
    print("\n4. Analyzing behavior...")
    snapshots = get_runtime_snapshots()
    
    if snapshots:
        latest = snapshots[-1]
        print(f"   Snapshot: {latest.snapshot_id}")
        print(f"   Nodes: {latest.graph.number_of_nodes()}")
        print(f"   Edges: {latest.graph.number_of_edges()}")
        
        # Extract features for health computation
        extractor = FeatureExtractor(snapshots)
        feature_matrix = extractor.build_feature_matrix()
        edge_features = feature_matrix.get("edges", [])
        
        # Compute health
        health_engine = ArchitectureHealthEngine(
            snapshots=snapshots,
            edge_features=edge_features
        )
        health = health_engine.compute()
        
        print(f"\n5. Architecture Health Report")
        print(f"   Overall Score: {health.get('overall_score', 0):.1f}/100")
        print(f"   Stability: {health.get('stability_index', 0):.2f}")
        print(f"   Risk Level: {health.get('risk_level', 'unknown')}")
        
        # Run forecasting
        forecast_engine = ArchitectureHealthForecaster()
        forecast = forecast_engine.forecast(steps_ahead=3)
        
        print(f"\n6. Health Forecast")
        predictions = forecast.get("forecast", [])
        for i, pred in enumerate(predictions):
            print(f"   Step {i+1}: {pred.get('health_score', 'N/A')}")
    else:
        print("   No snapshots available")
    
    print("\n" + "=" * 50)
    print("Example complete! ✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
