# ses_intelligence/narrative/synthesizer.py

def health_label(score: float) -> str:
    if score >= 80:
        return "Stable"
    elif score >= 60:
        return "Moderately Stable"
    elif score >= 40:
        return "Degrading"
    else:
        return "Critical"


def stability_label(index: float) -> str:
    if index >= 0.85:
        return "Highly Stable"
    elif index >= 0.70:
        return "Stable"
    elif index >= 0.50:
        return "Unstable"
    else:
        return "Highly Unstable"


def trend_label(slope: float) -> str:
    if slope > 2:
        return "Improving"
    elif slope > 0:
        return "Slightly Improving"
    elif slope == 0:
        return "Stable"
    elif slope > -2:
        return "Slightly Declining"
    else:
        return "Declining"


def urgency_level(score: float) -> str:
    if score >= 80:
        return "Low"
    elif score >= 60:
        return "Moderate"
    elif score >= 40:
        return "High"
    else:
        return "Critical"
