# ses_intelligence/narrative/forecast_summary.py

def summarize_forecast(forecast_data: dict) -> dict:
    """
    Expected format:
    {
        "current_health": 62,
        "predicted_health": 54,
        "days_ahead": 14,
        "threshold_breach_days": 16,
        "model_error": 4.2
    }
    """

    current = forecast_data.get("current_health", 0)
    predicted = forecast_data.get("predicted_health", 0)
    days = forecast_data.get("days_ahead", 0)
    breach = forecast_data.get("threshold_breach_days", None)
    error = forecast_data.get("model_error", 1)

    change = predicted - current

    if change < 0:
        direction = "decline"
    elif change > 0:
        direction = "improvement"
    else:
        direction = "stability"

    confidence = max(0, min(1, 1 - (error / 100)))

    narrative = (
        f"Projected {direction} of {abs(round(change, 2))} points "
        f"over {days} days."
    )

    if breach:
        narrative += f" Threshold breach expected in ~{breach} days."

    return {
        "summary": narrative,
        "confidence": round(confidence, 2)
    }
