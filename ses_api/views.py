import json
import os
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.runtime_state import get_runtime_snapshots
from ses_intelligence.tracing import get_edge_features

BASE_PATH = os.path.join(settings.BASE_DIR, "behavior_data", "architecture_health")


def load_json(filename):
    path = os.path.join(BASE_PATH, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


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
    forecast = load_json("forecast_output.json")
    return JsonResponse({
        "timestamp": datetime.utcnow(),
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
