import json
import os
import logging
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.confidence import ForecastConfidenceEngine
from ses_intelligence.runtime_state import get_runtime_snapshots
from ses_intelligence.tracing import get_edge_features

BASE_PATH = os.path.join(settings.BASE_DIR, "behavior_data", "architecture_health")
logger = logging.getLogger(__name__)


def load_json(filename):
    path = os.path.join(BASE_PATH, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _compute_forecast_from_history():
    history_path = os.path.join(BASE_PATH, "health_history.json")
    engine = ForecastConfidenceEngine(history_path=history_path, window_size=10)
    return engine.run()


def api_health(request):

    # Step 1 — Gather runtime state
    snapshots = get_runtime_snapshots()
    edge_features = get_edge_features()

    # Step 2 — Run full architecture engine
    engine = ArchitectureHealthEngine(
        snapshots=snapshots,
        edge_features=edge_features,
    )

    result = engine.compute()

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        **result
    })


def api_forecast(request):
    forecast = {}
    history = []

    try:
        persisted_forecast = load_json("forecast_output.json")
        if isinstance(persisted_forecast, dict) and persisted_forecast:
            forecast = persisted_forecast
        else:
            logger.warning(
                "Persisted forecast_output.json missing/empty; recomputing from health history",
                extra={"base_path": BASE_PATH},
            )
            forecast = _compute_forecast_from_history()
    except Exception:
        logger.exception("Failed to load or compute forecast", extra={"base_path": BASE_PATH})
        forecast = {
            "status": "error",
            "message": "Forecast computation failed",
        }

    # Load health history for the frontend
    try:
        history_path = os.path.join(BASE_PATH, "health_history.json")
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                history_data = json.load(f)
            
            # Extract relevant fields for frontend (timestamp and health_score)
            for entry in history_data:
                if isinstance(entry, dict):
                    # Try different possible field names for health score
                    health_score = (
                        entry.get("health_score") or
                        entry.get("architecture_health_score") or
                        entry.get("health", {}).get("architecture_health_score") or
                        entry.get("raw", {}).get("health_score") or
                        entry.get("raw", {}).get("architecture_health_score")
                    )
                    timestamp = entry.get("timestamp")
                    if health_score is not None and timestamp:
                        history.append({
                            "timestamp": timestamp,
                            "health_score": health_score
                        })
    except Exception:
        logger.exception("Failed to load health history", extra={"base_path": BASE_PATH})

    return JsonResponse({
        "timestamp": datetime.utcnow().isoformat(),
        "history": history,
        "forecast": forecast
    })


def api_impact(request):
    risk = load_json("risk_output.json")
    return JsonResponse({
        "timestamp": datetime.utcnow(),
        "impact_ranking": risk
    })


def api_graph(request):
    snapshot_path = os.path.join(settings.BASE_DIR, "behavior_data", "snapshots")

    if not os.path.exists(snapshot_path):
        return JsonResponse({"nodes": [], "edges": []})

    files = sorted(os.listdir(snapshot_path))
    if not files:
        return JsonResponse({"nodes": [], "edges": []})

    latest = os.path.join(snapshot_path, files[-1])

    with open(latest, "r") as f:
        graph = json.load(f)

    return JsonResponse({
        "timestamp": datetime.utcnow(),
        "nodes": graph.get("nodes", []),
        "edges": graph.get("edges", [])
    })


def api_executive(request):
    anomalies = load_json("risk_output.json")
    forecast = load_json("forecast_output.json")

    return JsonResponse({
        "timestamp": datetime.utcnow(),
        "summary": "Architecture shows predictive degradation signals.",
        "forecast_outlook": forecast,
        "risk_analysis": anomalies
    })
