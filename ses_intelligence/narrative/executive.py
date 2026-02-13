# ses_intelligence/narrative/executive.py

from .synthesizer import health_label, urgency_level


def generate_executive_summary(
    health_score: float,
    trend: str,
    risk_count: int,
    forecast_text: str
) -> str:

    label = health_label(health_score)
    urgency = urgency_level(health_score)

    summary = (
        f"Architecture status: {label}. "
        f"Trend: {trend}. "
        f"{risk_count} high-risk execution edges detected. "
        f"{forecast_text} "
        f"Operational urgency level: {urgency}."
    )

    return summary
