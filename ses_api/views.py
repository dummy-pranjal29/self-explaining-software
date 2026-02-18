import json
import os
import logging
import re
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.confidence import ForecastConfidenceEngine
from ses_intelligence.runtime_state import get_runtime_snapshots
from ses_intelligence.tracing import get_edge_features
from ses_intelligence.project_storage import ProjectStorage


logger = logging.getLogger(__name__)

# Input validation constants
VALID_PROJECT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
MAX_PROJECT_NAME_LENGTH = 100


class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: int = 400, error_code: str = "BAD_REQUEST"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


def validate_project_id(project_id: str) -> str:
    """
    Validate project_id format.
    
    Args:
        project_id: The project identifier to validate.
        
    Returns:
        The validated project_id.
        
    Raises:
        APIError: If project_id is invalid.
    """
    if not project_id:
        return 'default'
    
    if not VALID_PROJECT_ID_PATTERN.match(project_id):
        raise APIError(
            message=f"Invalid project_id format: '{project_id}'. "
                   f"Must be 1-64 alphanumeric characters, hyphens, or underscores.",
            status_code=400,
            error_code="INVALID_PROJECT_ID"
        )
    
    return project_id


def validate_project_name(name: str) -> str:
    """
    Validate project name.
    
    Args:
        name: The project name to validate.
        
    Returns:
        The validated name.
        
    Raises:
        APIError: If name is invalid.
    """
    if not name:
        return ""
    
    if len(name) > MAX_PROJECT_NAME_LENGTH:
        raise APIError(
            message=f"Project name too long: maximum {MAX_PROJECT_NAME_LENGTH} characters.",
            status_code=400,
            error_code="INVALID_PROJECT_NAME"
        )
    
    return name.strip()


def api_error_response(message: str, status_code: int = 400, error_code: str = "BAD_REQUEST", details: dict = None):
    """Create a standardized error response."""
    response = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    if details:
        response["error"]["details"] = details
    return JsonResponse(response, status=status_code)


def get_project_id_from_request(request) -> str:
    """Extract and validate project_id from request query parameters."""
    project_id = request.GET.get('project', 'default')
    try:
        return validate_project_id(project_id)
    except APIError as e:
        logger.warning(f"Invalid project_id: {project_id}")
        return 'default'  # Default to 'default' for invalid IDs


def get_project_storage(project_id: str) -> ProjectStorage:
    """Get project storage for the given project_id."""
    return ProjectStorage(project_id)


def load_json_for_project(project_id: str, filename: str) -> dict:
    """Load JSON file from project's health directory."""
    storage = get_project_storage(project_id)
    path = storage.health_dir / filename
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _compute_forecast_from_history(project_id: str = "default"):
    """Compute forecast for a specific project."""
    storage = get_project_storage(project_id)
    history_path = storage.snapshot_path
    engine = ForecastConfidenceEngine(history_path=str(history_path), window_size=10)
    return engine.run()


def api_health(request):
    """Get current architecture health for a project."""
    project_id = get_project_id_from_request(request)

    # Step 1 — Gather runtime state
    snapshots = get_runtime_snapshots()
    edge_features = get_edge_features()

    # Step 2 — Run full architecture engine with project_id
    engine = ArchitectureHealthEngine(
        snapshots=snapshots,
        edge_features=edge_features,
        project_id=project_id,
    )

    result = engine.compute()

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        **result
    })


def api_forecast(request):
    """Get forecast data for a project."""
    project_id = get_project_id_from_request(request)

    try:
        # Always compute fresh forecast from health history
        forecast = _compute_forecast_from_history(project_id)

    except Exception:
        logger.exception(
            "Failed to compute forecast",
            extra={"project_id": project_id},
        )
        forecast = {
            "status": "error",
            "message": "Forecast computation failed",
        }

    history = []

    try:
        storage = get_project_storage(project_id)
        history_path = storage.snapshot_path

        if history_path.exists():
            with open(history_path, "r") as f:
                history_data = json.load(f)

            for entry in history_data:
                if isinstance(entry, dict):

                    health_score = (
                        entry.get("health_score") or
                        entry.get("architecture_health_score") or
                        entry.get("raw", {}).get("health_score") or
                        entry.get("raw", {}).get("architecture_health_score")
                    )

                    # Get stability_index from entry or compute from raw data
                    stability_index = (
                        entry.get("stability_index") or
                        entry.get("raw", {}).get("stability_index") or
                        entry.get("raw", {}).get("stability", {}).get("index") or
                        None
                    )

                    timestamp = entry.get("timestamp")

                    if health_score is not None and timestamp:
                        history.append({
                            "timestamp": timestamp,
                            "health_score": health_score,
                            "stability_index": stability_index
                        })

    except Exception:
        logger.exception(
            "Failed to load health history",
            extra={"project_id": project_id},
        )

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "history": history,
        "forecast": forecast
    })


def api_impact(request):
    """Get impact ranking for a project."""
    project_id = get_project_id_from_request(request)
    risk = load_json_for_project(project_id, "risk_output.json")
    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "impact_ranking": risk
    })


def api_graph(request):
    """Get architecture graph for a project."""
    project_id = get_project_id_from_request(request)
    storage = get_project_storage(project_id)
    snapshot_path = storage.snapshots_dir

    if not snapshot_path.exists():
        return JsonResponse({
            "project_id": project_id,
            "nodes": [], 
            "edges": []
        })

    files = sorted(snapshot_path.glob("*.json"))
    if not files:
        return JsonResponse({
            "project_id": project_id,
            "nodes": [], 
            "edges": []
        })

    latest = files[-1]

    with open(latest, "r") as f:
        snapshot = json.load(f)

    edge_signature = snapshot.get("edge_signature", {})

    # Run stability computation using ArchitectureHealthEngine
    snapshots = get_runtime_snapshots()
    edge_features = get_edge_features()

    engine = ArchitectureHealthEngine(
        snapshots=snapshots,
        edge_features=edge_features,
        project_id=project_id,
    )

    health_result = engine.compute()

    stability_map = {}

    for edge in health_result.get("edges", []):
        key = f"{edge.get('source')}|{edge.get('target')}"
        stability_map[key] = {
            "stability_index": edge.get("stability_index", 0),
            "anomaly_flag": edge.get("anomaly_flag", False),
        }

    nodes = set()
    edges = []

    for edge_key, meta in edge_signature.items():

        src, dst = edge_key.split("|")

        nodes.add(src)
        nodes.add(dst)

        stability_data = stability_map.get(edge_key, {})

        edges.append({
            "source": src,
            "target": dst,
            "call_count": meta.get("call_count", 0),
            "avg_duration": meta.get("avg_duration", 0),
            "stability_index": stability_data.get("stability_index", 0),
            "anomaly_flag": stability_data.get("anomaly_flag", False),
        })

    node_list = [{"id": n} for n in nodes]

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "nodes": node_list,
        "edges": edges
    })


def api_executive(request):
    """Get executive summary for a project."""
    project_id = get_project_id_from_request(request)
    
    # Get health data from the engine
    snapshots = get_runtime_snapshots()
    edge_features = get_edge_features()
    
    engine = ArchitectureHealthEngine(
        snapshots=snapshots,
        edge_features=edge_features,
        project_id=project_id,
    )
    
    health_result = engine.compute()
    health_score = health_result.get("health_score", 50)
    
    # Get forecast for trend
    try:
        forecast_result = _compute_forecast_from_history(project_id)
        trend_value = forecast_result.get("trend", 0)
        # Ensure trend is a number for comparison
        trend = float(trend_value) if isinstance(trend_value, (int, float)) else 0
    except Exception:
        trend = 0
    
    # Count high-risk edges
    risk_count = 0
    edges = health_result.get("edges", [])
    for edge in edges:
        if edge.get("anomaly_flag", False):
            risk_count += 1
    
    # Get historical scores for trend analysis
    historical_scores = []
    try:
        from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
        history = ArchitectureHealthHistory(project_id=project_id)
        historical_scores = history.get_health_scores()
    except Exception:
        pass
    
    # Calculate trend slope
    trend_slope = 0
    if len(historical_scores) >= 2:
        n = len(historical_scores)
        sum_x = sum(range(n))
        sum_y = sum(historical_scores)
        sum_xy = sum(i * score for i, score in enumerate(historical_scores))
        sum_x2 = sum(i * i for i in range(n))
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator != 0:
            trend_slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    # Generate dynamic summary using narrative engine
    from ses_intelligence.narrative.executive import generate_executive_summary
    
    forecast_text = "Forecast indicates stable performance." if trend >= 0 else "Forecast indicates potential degradation."
    summary = generate_executive_summary(
        health_score=health_score,
        trend=trend_slope,
        risk_count=risk_count,
        forecast_text=forecast_text
    )
    
    # Get risk analysis and forecast data
    anomalies = load_json_for_project(project_id, "risk_output.json")
    forecast = load_json_for_project(project_id, "forecast_output.json")

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "summary": summary,
        "health_score": health_score,
        "trend_slope": trend_slope,
        "risk_count": risk_count,
        "forecast_outlook": forecast,
        "risk_analysis": anomalies,
        "historical_scores": historical_scores[-10:] if historical_scores else []
    })


# ----------------------------------------------------------
# PROJECT MANAGEMENT ENDPOINTS
# ----------------------------------------------------------

def api_projects_list(request):
    """List all projects."""
    try:
        projects = ProjectStorage.list_projects()
        logger.info(f"Listed projects: {len(projects)} found")
        return JsonResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "projects": projects,
            "count": len(projects)
        })
    except Exception as e:
        logger.exception("Failed to list projects")
        return api_error_response(
            message="Failed to retrieve projects list",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )


def api_project_create(request):
    """Create a new project."""
    import uuid
    
    # Validate request method
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to create a project.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
    # Get project name from request body or generate
    try:
        body = json.loads(request.body) if request.body else {}
        project_name = body.get('name', '')
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in project create request")
        return api_error_response(
            message="Invalid JSON in request body",
            status_code=400,
            error_code="INVALID_JSON"
        )
    
    # Validate project name
    try:
        project_name = validate_project_name(project_name)
    except APIError as e:
        return api_error_response(e.message, e.status_code, e.error_code)
    
    # Generate project ID
    project_id = str(uuid.uuid4())[:8]
    
    # Create project storage
    try:
        storage = ProjectStorage(project_id)
        logger.info(f"Created project: {project_id}")
    except Exception as e:
        logger.exception(f"Failed to create project storage: {project_id}")
        return api_error_response(
            message="Failed to create project storage",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
    
    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "name": project_name or f"Project {project_id}",
        "status": "created"
    })


def api_project_delete(request, project_id):
    """Delete a project."""
    # Validate project_id
    try:
        project_id = validate_project_id(project_id)
    except APIError as e:
        return api_error_response(e.message, e.status_code, e.error_code)
    
    # Prevent deletion of default project
    if project_id == 'default':
        return api_error_response(
            message="Cannot delete the default project",
            status_code=400,
            error_code="CANNOT_DELETE_DEFAULT"
        )
    
    # Delete the project
    try:
        success = ProjectStorage.delete_project(project_id)
        if success:
            logger.info(f"Deleted project: {project_id}")
        else:
            logger.warning(f"Project not found for deletion: {project_id}")
    except Exception as e:
        logger.exception(f"Failed to delete project: {project_id}")
        return api_error_response(
            message="Failed to delete project",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
    
    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "status": "deleted" if success else "not_found"
    })


# ----------------------------------------------------------
# LLM CHAT ENDPOINT
# ----------------------------------------------------------

@csrf_exempt
def api_chat(request):
    """
    LLM-powered chat endpoint for conversational intelligence.
    
    POST /api/v1/chat/
    Body: {"question": "What is the health trend?"}
    
    Returns: {"response": "...", "status": "success"}
    """
    project_id = get_project_id_from_request(request)
    
    # Validate request method
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to send a message.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
    # Parse request body
    try:
        body = json.loads(request.body) if request.body else {}
        question = body.get('question', '').strip()
    except json.JSONDecodeError:
        return api_error_response(
            message="Invalid JSON in request body",
            status_code=400,
            error_code="INVALID_JSON"
        )
    
    if not question:
        return api_error_response(
            message="Question is required",
            status_code=400,
            error_code="MISSING_QUESTION"
        )
    
    try:
        # Import LLM service
        from ses_intelligence.llm import get_llm_service
        
        # Gather project data
        storage = get_project_storage(project_id)
        
        # Get health data
        health_data = {}
        try:
            health_path = storage.health_dir / "health_history.json"
            if health_path.exists():
                with open(health_path, 'r') as f:
                    health_history = json.load(f)
                if isinstance(health_history, list) and health_history:
                    health_data = health_history[-1].get('raw', {})
        except Exception:
            logger.exception("Failed to load health data")
        
        # Get forecast data
        forecast_data = {}
        try:
            forecast_result = _compute_forecast_from_history(project_id)
            forecast_data = forecast_result
        except Exception:
            logger.exception("Failed to compute forecast")
        
        # Get historical scores
        historical_scores = []
        try:
            from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
            history = ArchitectureHealthHistory(project_id=project_id)
            historical_scores = history.get_health_scores()
        except Exception:
            logger.exception("Failed to load historical scores")
        
        # Get recommendations
        recommendations = health_data.get('recommendations', [])
        
        # Get project name
        project_name = project_id
        
        # Get LLM service and make request
        llm_service = get_llm_service()
        result = llm_service.get_response(
            project_id=project_id,
            project_name=project_name,
            health_data=health_data,
            forecast_data=forecast_data,
            historical_scores=historical_scores,
            recommendations=recommendations,
            question=question,
        )
        
        return JsonResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "question": question,
            **result
        })
        
    except Exception as e:
        logger.exception("Chat endpoint error")
        return api_error_response(
            message=f"Chat processing failed: {str(e)}",
            status_code=500,
            error_code="CHAT_ERROR"
        )
