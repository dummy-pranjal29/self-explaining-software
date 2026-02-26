"""
SES Intelligence Web Views

This module contains all the API views for the embedded Django server.
It provides endpoints for architecture health, forecasting, and AI chat.
"""

import json
import logging
import re
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
    """Validate project_id format."""
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
    """Validate project name."""
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
        return 'default'


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

    snapshots = get_runtime_snapshots()
    edge_features = get_edge_features()

    engine = ArchitectureHealthEngine(
        snapshots=snapshots,
        edge_features=edge_features,
        project_id=project_id,
    )

    result = engine.compute()
    
    # Always ensure health_score is present even if no snapshots
    if "health_score" not in result:
        # Try to load from history if no current snapshots
        try:
            from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
            history = ArchitectureHealthHistory(project_id=project_id)
            historical = history.get_health_scores()
            if historical:
                result["health_score"] = historical[-1]
                result["architecture_health_score"] = historical[-1]
            else:
                result["health_score"] = 50
                result["architecture_health_score"] = 50
        except Exception:
            result["health_score"] = 50
            result["architecture_health_score"] = 50
    
    # Ensure required fields have defaults
    if result.get("stability_index") is None:
        result["stability_index"] = 0.5
    if result.get("risk_count") is None and result.get("anomaly_count") is not None:
        result["risk_count"] = result.get("anomaly_count", 0)
    if result.get("risk_count") is None:
        result["risk_count"] = 0

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        **result
    })


def api_forecast(request):
    """Get forecast data for a project."""
    project_id = get_project_id_from_request(request)

    try:
        forecast = _compute_forecast_from_history(project_id)
    except Exception:
        logger.exception("Failed to compute forecast", extra={"project_id": project_id})
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
        logger.exception("Failed to load health history", extra={"project_id": project_id})

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
    
    snapshots = get_runtime_snapshots()
    edge_features = get_edge_features()
    
    engine = ArchitectureHealthEngine(
        snapshots=snapshots,
        edge_features=edge_features,
        project_id=project_id,
    )
    
    health_result = engine.compute()
    health_score = health_result.get("health_score", 50)
    
    try:
        forecast_result = _compute_forecast_from_history(project_id)
        trend_value = forecast_result.get("trend", 0)
        trend = float(trend_value) if isinstance(trend_value, (int, float)) else 0
    except Exception:
        trend = 0
    
    risk_count = 0
    edges = health_result.get("edges", [])
    for edge in edges:
        if edge.get("anomaly_flag", False):
            risk_count += 1
    
    historical_scores = []
    try:
        from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
        history = ArchitectureHealthHistory(project_id=project_id)
        historical_scores = history.get_health_scores()
    except Exception:
        pass
    
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
    
    from ses_intelligence.narrative.executive import generate_executive_summary
    
    forecast_text = "Forecast indicates stable performance." if trend >= 0 else "Forecast indicates potential degradation."
    summary = generate_executive_summary(
        health_score=health_score,
        trend=trend_slope,
        risk_count=risk_count,
        forecast_text=forecast_text
    )
    
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
    
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to create a project.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
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
    
    try:
        project_name = validate_project_name(project_name)
    except APIError as e:
        return api_error_response(e.message, e.status_code, e.error_code)
    
    project_id = str(uuid.uuid4())[:8]
    
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
    try:
        project_id = validate_project_id(project_id)
    except APIError as e:
        return api_error_response(e.message, e.status_code, e.error_code)
    
    if project_id == 'default':
        return api_error_response(
            message="Cannot delete the default project",
            status_code=400,
            error_code="CANNOT_DELETE_DEFAULT"
        )
    
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


@csrf_exempt
def api_chat(request):
    """
    LLM-powered chat endpoint for conversational intelligence.
    
    POST /api/v1/chat/
    Body: {"question": "What is the health trend?"}
    
    Returns: {"response": "...", "status": "success"}
    """
    project_id = get_project_id_from_request(request)
    
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to send a message.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
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
        from ses_intelligence.llm import get_llm_service
        
        storage = get_project_storage(project_id)
        
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
        
        forecast_data = {}
        try:
            forecast_result = _compute_forecast_from_history(project_id)
            forecast_data = forecast_result
        except Exception:
            logger.exception("Failed to compute forecast")
        
        historical_scores = []
        try:
            from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
            history = ArchitectureHealthHistory(project_id=project_id)
            historical_scores = history.get_health_scores()
        except Exception:
            logger.exception("Failed to load historical scores")
        
        recommendations = health_data.get('recommendations', [])
        project_name = project_id
        
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


def api_config(request):
    """
    Get UI configuration - available views, endpoints, and features.
    This allows the frontend to dynamically render only what the backend supports.
    """
    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "available_views": [
            {"id": "dashboard", "label": "Dashboard", "default": True},
            {"id": "health", "label": "Health"},
            {"id": "forecast", "label": "Forecast"},
            {"id": "architecture", "label": "Architecture"},
            {"id": "api", "label": "API"},
        ],
        "available_endpoints": [
            {"method": "GET", "path": "/api/v1/health/", "description": "Get architecture health"},
            {"method": "GET", "path": "/api/v1/forecast/", "description": "Get forecast data"},
            {"method": "GET", "path": "/api/v1/graph/", "description": "Get architecture graph"},
            {"method": "GET", "path": "/api/v1/executive/", "description": "Get executive summary"},
            {"method": "GET", "path": "/api/v1/projects/", "description": "List all projects"},
            {"method": "POST", "path": "/api/v1/projects/create/", "description": "Create a new project"},
            {"method": "DELETE", "path": "/api/v1/projects/delete/{id}/", "description": "Delete a project"},
            {"method": "POST", "path": "/api/v1/chat/", "description": "AI Chat assistant"},
        ],
        "features": {
            "projects": True,
            "create_project": True,
            "delete_project": True,
            "chat": True,
            "forecast": True,
            "graph": True,
            "impact": True,
        }
    })


# In-memory agent registry (for production, use database)
_agent_registry = {}


def api_agent_register(request):
    """
    Register a remote agent (local machine) with the centralized server.
    
    POST /api/v1/agent/register/
    Body: {
        "agent_id": "unique-agent-id",
        "agent_name": "My Local Machine",
        "project_id": "project-to-monitor"
    }
    
    Returns: {"agent_id": "...", "status": "registered"}
    """
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to register an agent.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
    try:
        body = json.loads(request.body) if request.body else {}
        agent_id = body.get('agent_id', '')
        agent_name = body.get('agent_name', 'Unnamed Agent')
        project_id = body.get('project_id', 'default')
    except json.JSONDecodeError:
        return api_error_response(
            message="Invalid JSON in request body",
            status_code=400,
            error_code="INVALID_JSON"
        )
    
    if not agent_id:
        return api_error_response(
            message="agent_id is required",
            status_code=400,
            error_code="MISSING_AGENT_ID"
        )
    
    try:
        project_id = validate_project_id(project_id)
    except APIError as e:
        return api_error_response(e.message, e.status_code, e.error_code)
    
    # Register the agent
    _agent_registry[agent_id] = {
        'agent_id': agent_id,
        'agent_name': agent_name,
        'project_id': project_id,
        'registered_at': datetime.utcnow().isoformat(),
        'last_heartbeat': datetime.utcnow().isoformat(),
        'status': 'online'
    }
    
    logger.info(f"Registered agent: {agent_id} for project: {project_id}")
    
    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "registered",
        "message": f"Agent '{agent_name}' registered successfully"
    })


def api_agent_heartbeat(request):
    """
    Receive health data from a remote agent.
    
    POST /api/v1/agent/heartbeat/
    Body: {
        "agent_id": "unique-agent-id",
        "health_data": {...},
        "snapshots": [...],
        "graph_data": {...}
    }
    
    Returns: {"status": "success"}
    """
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to send heartbeat.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
    try:
        body = json.loads(request.body) if request.body else {}
        agent_id = body.get('agent_id', '')
        health_data = body.get('health_data', {})
        snapshots_data = body.get('snapshots', [])
        graph_data = body.get('graph_data', {})
    except json.JSONDecodeError:
        return api_error_response(
            message="Invalid JSON in request body",
            status_code=400,
            error_code="INVALID_JSON"
        )
    
    if agent_id not in _agent_registry:
        return api_error_response(
            message=f"Agent '{agent_id}' not registered. Call /agent/register/ first.",
            status_code=404,
            error_code="AGENT_NOT_FOUND"
        )
    
    agent = _agent_registry[agent_id]
    project_id = agent['project_id']
    
    # Store the health data for this agent
    storage = get_project_storage(project_id)
    
    try:
        # Save health data
        health_path = storage.health_dir / f"agent_{agent_id}_health.json"
        with open(health_path, 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': agent_id,
                'health_data': health_data,
                'snapshots': snapshots_data,
                'graph_data': graph_data
            }, f, indent=2)
        
        # Update agent status
        agent['last_heartbeat'] = datetime.utcnow().isoformat()
        agent['status'] = 'online'
        
        # Save to agent-specific history
        agent_history_path = storage.health_dir / f"agent_{agent_id}_history.json"
        history = []
        if agent_history_path.exists():
            with open(agent_history_path, 'r') as f:
                history = json.load(f)
        
        history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'health_data': health_data
        })
        
        # Keep only last 100 entries
        history = history[-100:]
        
        with open(agent_history_path, 'w') as f:
            json.dump(history, f)
        
        logger.info(f"Heartbeat received from agent: {agent_id}")
        
        return JsonResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "status": "success",
            "message": "Health data received"
        })
        
    except Exception as e:
        logger.exception(f"Failed to store agent data: {agent_id}")
        return api_error_response(
            message=f"Failed to store agent data: {str(e)}",
            status_code=500,
            error_code="STORE_ERROR"
        )


def api_agent_list(request):
    """List all registered agents."""
    project_id = get_project_id_from_request(request)
    
    agents = []
    for agent_id, agent in _agent_registry.items():
        if agent.get('project_id') == project_id:
            agents.append({
                'agent_id': agent_id,
                'agent_name': agent.get('agent_name'),
                'registered_at': agent.get('registered_at'),
                'last_heartbeat': agent.get('last_heartbeat'),
                'status': agent.get('status')
            })
    
    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "agents": agents,
        "count": len(agents)
    })


def api_agent_unregister(request):
    """Unregister an agent."""
    if request.method != 'POST':
        return api_error_response(
            message="Method not allowed. Use POST to unregister.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
    try:
        body = json.loads(request.body) if request.body else {}
        agent_id = body.get('agent_id', '')
    except json.JSONDecodeError:
        return api_error_response(
            message="Invalid JSON in request body",
            status_code=400,
            error_code="INVALID_JSON"
        )
    
    if agent_id in _agent_registry:
        del _agent_registry[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
        return JsonResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "status": "unregistered"
        })
    
    return api_error_response(
        message=f"Agent '{agent_id}' not found",
        status_code=404,
        error_code="AGENT_NOT_FOUND"
    )


def serve_index(request):
    """Serve the React SPA index.html for all non-API routes."""
    from django.http import HttpResponse
    from pathlib import Path
    
    # Try to find the static index.html relative to this file
    try:
        package_dir = Path(__file__).resolve().parent
        index_path = package_dir / 'static' / 'index.html'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html')
    except Exception:
        pass
    
    # Fallback: return a simple HTML page
    return HttpResponse("""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SES Intelligence</title>
    <style>
      body { 
        background: #0a0a0a; 
        color: #f5f5f5; 
        font-family: monospace;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        margin: 0;
      }
      .loading { text-align: center; }
      .spinner { 
        width: 40px; 
        height: 40px; 
        border: 3px solid #333;
        border-top-color: #00ff88;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
      }
      @keyframes spin { to { transform: rotate(360deg); } }
    </style>
  </head>
  <body>
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading SES Intelligence Dashboard...</p>
    </div>
  </body>
</html>
    """, content_type='text/html')
