"""
FastAPI Example - SES Intelligence SDK

This example demonstrates using ses-intelligence with FastAPI.

Usage:
    pip install ses-intelligence[fastapi]
    uvicorn app:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ses_intelligence import initialize, trace_behavior, get_runtime_snapshots
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.forecasting import ArchitectureHealthForecaster

# Initialize SES with your project ID
initialize(
    project_id="fastapi-app",
    enable_forecasting=True,
)

app = FastAPI(title="SES Intelligence FastAPI Example")


class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    status: str


@trace_behavior
def create_user_record(name: str, email: str) -> dict:
    """Create a user record with tracing."""
    validate_email(email)
    save_to_db(name, email)
    send_notification(email)
    return {"id": 1, "name": name, "email": email, "status": "created"}


@trace_behavior
def validate_email(email: str) -> bool:
    """Validate email format."""
    if "@" not in email:
        raise ValueError("Invalid email")
    return True


@trace_behavior
def save_to_db(name: str, email: str) -> None:
    """Simulate database save."""
    pass


@trace_behavior
def send_notification(email: str) -> None:
    """Send notification."""
    pass


@trace_behavior
def get_user_record(user_id: int) -> dict:
    """Get user by ID."""
    fetch_from_db(user_id)
    enrich_user(user_id)
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}


@trace_behavior
def fetch_from_db(user_id: int) -> None:
    """Simulate DB fetch."""
    pass


@trace_behavior
def enrich_user(user_id: int) -> None:
    """Enrich user data."""
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SES Intelligence FastAPI Example", "status": "ok"}


@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user."""
    result = create_user_record(user.name, user.email)
    return UserResponse(**result, status="created")


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    result = get_user_record(user_id)
    return result


@app.get("/health")
async def health_check():
    """Health check with architecture metrics."""
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
        health_data["stability_index"] = health.get("stability_index", 0)
        
        # Forecast
        forecast_engine = ArchitectureHealthForecaster()
        forecast = forecast_engine.forecast(steps_ahead=3)
        health_data["forecast_direction"] = forecast.get("direction", "unknown")
    
    return health_data


@app.get("/stats")
async def get_stats():
    """Get architecture statistics."""
    snapshots = get_runtime_snapshots()
    
    if not snapshots:
        return {"message": "No data available"}
    
    latest = snapshots[-1]
    return {
        "nodes": latest.graph.number_of_nodes(),
        "edges": latest.graph.number_of_edges(),
        "snapshot_id": latest.snapshot_id,
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("SES Intelligence - FastAPI Example")
    print("=" * 50)
    print("\nStarting FastAPI server on http://localhost:8000")
    print("\nTest endpoints:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/users/")
    print("  - http://localhost:8000/users/1")
    print("  - http://localhost:8000/health")
    print("  - http://localhost:8000/stats")
    print("\nPress Ctrl+C to stop")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
