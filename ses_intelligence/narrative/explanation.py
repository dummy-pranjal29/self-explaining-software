"""
ses_intelligence/narrative/explanation.py

Enhanced AI Explanation Module

Provides comprehensive, narrative-style explanations that include:
- What changed
- Why it matters
- Risk level
- Suggested action
- Future outlook
- Severity tone
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class SeverityTone(Enum):
    """Tone based on severity of the issue."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    POSITIVE = "positive"


class RiskLevel(Enum):
    """Risk classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChangeExplanation:
    """A single change explanation with full context."""
    what_changed: str
    why_it_matters: str
    risk_level: RiskLevel
    suggested_action: str
    future_outlook: str
    severity_tone: SeverityTone
    confidence: float = 0.8


@dataclass
class ComprehensiveExplanation:
    """Complete explanation report with multiple sections."""
    timestamp: str
    overall_status: str
    health_score: float
    trend: str
    changes: List[ChangeExplanation]
    risk_summary: str
    recommended_actions: List[str]
    forecast_outlook: str
    severity_tone: SeverityTone
    confidence: float


def assess_risk_level(
    health_score: float,
    trend_slope: float,
    anomaly_count: int
) -> RiskLevel:
    """Assess overall risk level based on multiple factors."""
    if health_score < 30 or anomaly_count > 5:
        return RiskLevel.CRITICAL
    elif health_score < 50 or trend_slope < -3:
        return RiskLevel.HIGH
    elif health_score < 70 or anomaly_count > 0:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def get_severity_tone(risk_level: RiskLevel) -> SeverityTone:
    """Map risk level to appropriate tone."""
    tone_map = {
        RiskLevel.CRITICAL: SeverityTone.CRITICAL,
        RiskLevel.HIGH: SeverityTone.WARNING,
        RiskLevel.MEDIUM: SeverityTone.WARNING,
        RiskLevel.LOW: SeverityTone.POSITIVE,
    }
    return tone_map.get(risk_level, SeverityTone.INFO)


def explain_new_edge(
    caller: str,
    callee: str,
    call_count: int,
    avg_duration: float,
    confidence: float = 0.85
) -> ChangeExplanation:
    """Explain a new execution path that was detected."""
    return ChangeExplanation(
        what_changed=f"New execution path detected: `{caller}` now calls `{callee}`",
        why_it_matters=f"This represents a new behavior pattern with {call_count} invocations. "
                      f"This could indicate a feature change, refactoring, or unintended coupling.",
        risk_level=RiskLevel.MEDIUM if call_count < 10 else RiskLevel.LOW,
        suggested_action="Review if this new call path is intentional. "
                       "Verify it aligns with current architectural design principles.",
        future_outlook="Monitor this edge over time. If call frequency increases, "
                      "consider if this represents organic growth or potential technical debt.",
        severity_tone=SeverityTone.INFO,
        confidence=confidence
    )


def explain_removed_edge(
    caller: str,
    callee: str,
    previous_count: int,
    confidence: float = 0.85
) -> ChangeExplanation:
    """Explain a removed execution path."""
    return ChangeExplanation(
        what_changed=f"Execution path removed: `{caller}` no longer calls `{callee}`",
        why_it_matters=f"This call previously executed {previous_count} times. "
                      f"Its removal may indicate feature removal, error handling changes, "
                      f"or refactoring that simplified the call graph.",
        risk_level=RiskLevel.HIGH if previous_count > 50 else RiskLevel.MEDIUM,
        suggested_action="Verify this removal is intentional. Check if related functionality "
                       "was deprecated or moved to a different service.",
        future_outlook="If this was unintentional, monitor for broken functionality. "
                      "If intentional, this may improve system simplicity.",
        severity_tone=SeverityTone.WARNING,
        confidence=confidence
    )


def explain_duration_change(
    caller: str,
    callee: str,
    old_duration: float,
    new_duration: float,
    delta_pct: float,
    confidence: float = 0.8
) -> ChangeExplanation:
    """Explain a performance change in an existing edge."""
    is_slower = delta_pct > 0
    
    if abs(delta_pct) < 10:
        risk = RiskLevel.LOW
        tone = SeverityTone.POSITIVE
        action = "No action needed. Performance variation is within normal bounds."
        outlook = "Continue monitoring for sustained changes."
    elif abs(delta_pct) < 30:
        risk = RiskLevel.MEDIUM
        tone = SeverityTone.WARNING if is_slower else SeverityTone.POSITIVE
        if is_slower:
            action = "Investigate the cause of the performance change. Check for new dependencies or data volume changes."
            outlook = "Performance should stabilize if the change was temporary. Monitor for further degradation."
        else:
            action = "Performance improved. No immediate action needed."
            outlook = "Performance improvements confirmed."
    else:
        risk = RiskLevel.HIGH if is_slower else RiskLevel.LOW
        if is_slower:
            tone = SeverityTone.CRITICAL
            action = "URGENT: Significant performance degradation detected. Immediate investigation required to identify root cause."
            outlook = "Without intervention, this trend may continue. Consider rolling back recent changes if degradation persists."
        else:
            tone = SeverityTone.POSITIVE
            action = "Performance improved significantly. Continue monitoring."
            outlook = "Performance gains appear stable."
    
    return ChangeExplanation(
        what_changed=f"`{caller} → {callee}` execution time changed: "
                    f"{old_duration:.2f}ms → {new_duration:.2f}ms ({delta_pct:+.1f}%)",
        why_it_matters=f"{'Performance degradation may impact user experience' if is_slower else 'Performance improved, reducing resource consumption'}. "
                      f"This edge handles critical execution paths.",
        risk_level=risk,
        suggested_action=action,
        future_outlook=outlook,
        severity_tone=tone,
        confidence=confidence
    )


def explain_anomaly(
    edge: str,
    anomaly_type: str,
    details: Dict[str, Any],
    confidence: float = 0.75
) -> ChangeExplanation:
    """Explain an anomaly detected in the system."""
    caller, callee = edge.split("|") if "|" in edge else (edge, "unknown")
    
    anomaly_descriptions = {
        "spike": {
            "what": f"Unusual spike in call frequency detected for `{caller} → {callee}`",
            "why": "This could indicate a runaway loop, retry storm, or external attack.",
            "risk": RiskLevel.CRITICAL,
            "action": "Immediately investigate the cause. Check for error loops, "
                     "external service issues, or configuration problems.",
            "outlook": "Without resolution, this could lead to resource exhaustion "
                      "and service degradation."
        },
        "drop": {
            "what": f"Significant drop in call frequency for `{caller} → {callee}`",
            "why": "This could indicate service failures, circuit breaker activation, "
                  "or upstream issues.",
            "risk": RiskLevel.HIGH,
            "action": "Check downstream service health. Verify circuit breakers "
                     "haven't activated unnecessarily.",
            "outlook": "Monitor for recovery. If sustained, investigate "
                      "for service degradation or availability issues."
        },
        "latency": {
            "what": f"Latency anomaly detected in `{caller} → {callee}`",
            "why": "This could indicate resource contention, database issues, "
                  "or external dependency problems.",
            "risk": RiskLevel.HIGH,
            "action": "Investigate resource utilization and external dependencies. "
                     "Check for database locks, memory pressure, or network issues.",
            "outlook": "May resolve spontaneously or indicate underlying infrastructure issues."
        }
    }
    
    info = anomaly_descriptions.get(anomaly_type, anomaly_descriptions["latency"])
    
    return ChangeExplanation(
        what_changed=info["what"],
        why_it_matters=info["why"],
        risk_level=info["risk"],
        suggested_action=info["action"],
        future_outlook=info["outlook"],
        severity_tone=SeverityTone.CRITICAL if info["risk"] == RiskLevel.CRITICAL else SeverityTone.WARNING,
        confidence=confidence
    )


def generate_comprehensive_explanation(
    health_score: float,
    trend_slope: float,
    anomaly_count: int,
    new_edges: List[tuple],
    removed_edges: List[tuple],
    changed_edges: Dict[tuple, Dict],
    forecast_data: Optional[Dict] = None,
    confidence: float = 0.8
) -> ComprehensiveExplanation:
    """Generate a comprehensive explanation combining all factors."""
    
    from .synthesizer import health_label, trend_label, urgency_level
    
    changes: List[ChangeExplanation] = []
    
    # Process new edges
    for caller, callee, count, duration in new_edges:
        changes.append(explain_new_edge(caller, callee, count, duration))
    
    # Process removed edges
    for caller, callee, prev_count in removed_edges:
        changes.append(explain_removed_edge(caller, callee, prev_count))
    
    # Process duration changes
    for (caller, callee), data in changed_edges.items():
        changes.append(explain_duration_change(
            caller, callee,
            data.get("old_avg", 0),
            data.get("new_avg", 0),
            data.get("delta_pct", 0)
        ))
    
    # Determine overall risk and tone
    risk_level = assess_risk_level(health_score, trend_slope, anomaly_count)
    severity_tone = get_severity_tone(risk_level)
    
    # Generate recommended actions
    recommended_actions = []
    if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        recommended_actions.append("Immediate investigation required for critical issues")
    if anomaly_count > 0:
        recommended_actions.append(f"Review {anomaly_count} detected anomalies")
    if trend_slope < -2:
        recommended_actions.append("Implement corrective measures to reverse degradation trend")
    if health_score < 60:
        recommended_actions.append("Schedule architecture review to identify root causes")
    if not recommended_actions:
        recommended_actions.append("Continue monitoring - no immediate action required")
    
    # Generate forecast outlook
    if forecast_data:
        forecast_outlook = f"Forecast predicts {'improvement' if forecast_data.get('forecast_next', 0) > health_score else 'continued degradation'}"
    else:
        trend = trend_label(trend_slope)
        forecast_outlook = f"Based on current trend ({trend}), monitor for changes"
    
    return ComprehensiveExplanation(
        timestamp="",
        overall_status=health_label(health_score),
        health_score=health_score,
        trend=trend_label(trend_slope),
        changes=changes,
        risk_summary=f"{urgency_level(health_score)} urgency - {anomaly_count} anomalies detected",
        recommended_actions=recommended_actions,
        forecast_outlook=forecast_outlook,
        severity_tone=severity_tone,
        confidence=confidence
    )


def format_explanation_as_markdown(explanation: ComprehensiveExplanation) -> str:
    """Format the comprehensive explanation as markdown."""
    lines = []
    
    # Header
    lines.append(f"# Architecture Intelligence Report")
    lines.append("")
    lines.append(f"**Status:** {explanation.overall_status}")
    lines.append(f"**Health Score:** {explanation.health_score:.1f}/100")
    lines.append(f"**Trend:** {explanation.trend}")
    lines.append(f"**Risk Level:** {explanation.severity_tone.value.upper()}")
    lines.append(f"**Confidence:** {explanation.confidence * 100:.0f}%")
    lines.append("")
    
    # Changes section
    if explanation.changes:
        lines.append("## What Changed")
        lines.append("")
        for i, change in enumerate(explanation.changes, 1):
            lines.append(f"### {i}. {change.what_changed}")
            lines.append(f"   - **Why it matters:** {change.why_it_matters}")
            lines.append(f"   - **Risk:** {change.risk_level.value}")
            lines.append(f"   - **Suggested Action:** {change.suggested_action}")
            lines.append(f"   - **Future Outlook:** {change.future_outlook}")
            lines.append("")
    
    # Recommended actions
    lines.append("## Recommended Actions")
    lines.append("")
    for action in explanation.recommended_actions:
        lines.append(f"- {action}")
    lines.append("")
    
    # Forecast
    lines.append("## Future Outlook")
    lines.append("")
    lines.append(explanation.forecast_outlook)
    lines.append("")
    
    return "\n".join(lines)
