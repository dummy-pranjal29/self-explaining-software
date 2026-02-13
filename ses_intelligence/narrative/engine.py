# ses_intelligence/narrative/engine.py

import json
import os

from .synthesizer import health_label, trend_label
from .drivers import analyze_risk_edges
from .forecast_summary import summarize_forecast
from .executive import generate_executive_summary


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
HEALTH_PATH = os.path.join(BASE_DIR, "behavior_data", "architecture_health", "health_history.json")
RISK_PATH = os.path.join(BASE_DIR, "behavior_data", "architecture_health", "risk_output.json")
FORECAST_PATH = os.path.join(BASE_DIR, "behavior_data", "architecture_health", "forecast_output.json")


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def generate_narrative():

    health_data = load_json(HEALTH_PATH)
    risk_data = load_json(RISK_PATH)
    forecast_data = load_json(FORECAST_PATH)

    # --------------------------------------------------
    # HEALTH EXTRACTION (ALIGNED WITH YOUR STRUCTURE)
    # --------------------------------------------------

    current_health = 0
    trend_slope = 0

    if isinstance(health_data, list) and len(health_data) > 0:
        latest_entry = health_data[-1]

        health_block = latest_entry.get("health", {})
        current_health = health_block.get("architecture_health_score", 0)

        # Optional future support
        trend_slope = latest_entry.get("trend_slope", 0)

    elif isinstance(health_data, dict):
        current_health = health_data.get("architecture_health_score", 0)
        trend_slope = health_data.get("trend_slope", 0)

    # --------------------------------------------------

    health_state = health_label(current_health)
    trend_state = trend_label(trend_slope)

    drivers = analyze_risk_edges(risk_data)
    forecast = summarize_forecast(forecast_data)

    executive_summary = generate_executive_summary(
        current_health,
        trend_state,
        len(drivers),
        forecast["summary"]
    )

    return {
        "health_state": health_state,
        "health_score": round(current_health, 2),
        "trend": trend_state,
        "risk_drivers": drivers,
        "forecast": forecast,
        "executive_summary": executive_summary,
        "confidence": forecast["confidence"]
    }
