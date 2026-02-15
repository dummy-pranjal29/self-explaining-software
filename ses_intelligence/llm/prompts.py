"""
System prompts for the LLM conversational assistant.

These prompts define the assistant's role and constraints.
"""

SYSTEM_PROMPT = """You are the Self-Evolving Software (SES) Assistant, an AI assistant 
specialized in software architecture analysis and health prediction.

Your role:
- Explain architecture health metrics in plain English
- Interpret forecasting results and their implications
- Summarize risk indicators and their business impact
- Answer questions about software architecture trends

CRITICAL RULES:
1. NEVER perform calculations yourself - use the provided mathematical data
2. Always ground your explanations in the actual metrics provided
3. If data is insufficient, explain what additional information would be needed
4. Use precise terminology but explain it for a technical audience
5. Provide actionable insights based on the metrics

You have access to:
- Current architecture health score (0.0-1.0)
- Historical health scores and trends
- Forecast predictions with confidence intervals
- Risk indicators and impact analysis
- Component-level scores (stability, complexity, coupling)

When answering questions:
- Be specific about the metrics
- Explain what the numbers mean in context
- Highlight trends and patterns
- Suggest actionable recommendations based on the data
"""


CONTEXT_TEMPLATE = """
Current Project: {project_name}
Project ID: {project_id}

Architecture Health:
- Overall Score: {health_score}
- Stability: {stability_score}
- Complexity: {complexity_score}
- Coupling: {coupling_score}

Risk Level: {risk_level}
Risk Indicators: {risk_indicators}

Forecast:
- Predicted Next Score: {forecast_next}
- Confidence Score: {confidence_score}
- Confidence Interval: [{ci_lower}, {ci_upper}]
- Volatility: {volatility}
- Status: {forecast_status}

Historical Trend:
{historical_summary}

Recent Recommendations:
{recommendations}

---

Question: {question}

Please provide a clear, actionable answer based on the metrics above.
"""


def build_context(
    project_name: str,
    project_id: str,
    health_data: dict,
    forecast_data: dict,
    historical_scores: list,
    recommendations: list,
    question: str,
) -> str:
    """
    Build context string from available data.
    
    Args:
        project_name: Human-readable project name
        project_id: Project identifier
        health_data: Current health metrics
        forecast_data: Forecast results
        historical_scores: List of historical health scores
        recommendations: List of recommendations
        question: User's question
        
    Returns:
        Formatted context string
    """
    # Extract health values with defaults
    health_score = health_data.get('health_score', 'N/A')
    component_scores = health_data.get('component_scores', {})
    stability = component_scores.get('stability', 'N/A')
    complexity = component_scores.get('complexity', 'N/A')
    coupling = component_scores.get('coupling', 'N/A')
    risk_level = health_data.get('risk_level', 'unknown')
    risk_indicators = health_data.get('risk_indicators', [])
    
    # Extract forecast values with defaults
    forecast_status = forecast_data.get('status', 'unknown')
    forecast_next = forecast_data.get('forecast_next', 'N/A')
    confidence = forecast_data.get('confidence_score', forecast_data.get('confidence_score', 'N/A'))
    ci = forecast_data.get('confidence_interval', {})
    ci_lower = ci.get('lower', 'N/A')
    ci_upper = ci.get('upper', 'N/A')
    volatility = forecast_data.get('volatility', 'unknown')
    
    # Build historical summary
    if historical_scores:
        scores_str = ', '.join([f"{s:.2f}" for s in historical_scores[-10:]])
        historical_summary = f"Recent scores: {scores_str}"
        
        if len(historical_scores) >= 3:
            recent = historical_scores[-3:]
            trend = "improving" if recent[-1] > recent[0] else "declining"
            historical_summary += f" | Trend: {trend}"
    else:
        historical_summary = "No historical data available"
    
    # Format risk indicators
    if risk_indicators:
        risk_str = ", ".join([str(r) for r in risk_indicators[:5]])
        if len(risk_indicators) > 5:
            risk_str += f" ... and {len(risk_indicators) - 5} more"
    else:
        risk_str = "None"
    
    # Format recommendations
    if recommendations:
        rec_str = "\n".join([f"- {r}" for r in recommendations[:5]])
    else:
        rec_str = "No recommendations available"
    
    return CONTEXT_TEMPLATE.format(
        project_name=project_name,
        project_id=project_id,
        health_score=f"{health_score:.2f}" if isinstance(health_score, (int, float)) else health_score,
        stability_score=f"{stability:.2f}" if isinstance(stability, (int, float)) else stability,
        complexity_score=f"{complexity:.2f}" if isinstance(complexity, (int, float)) else complexity,
        coupling_score=f"{coupling:.2f}" if isinstance(coupling, (int, float)) else coupling,
        risk_level=risk_level,
        risk_indicators=risk_str,
        forecast_next=f"{forecast_next:.2f}" if isinstance(forecast_next, (int, float)) else forecast_next,
        confidence_score=f"{confidence:.2f}" if isinstance(confidence, (int, float)) else confidence,
        ci_lower=f"{ci_lower:.2f}" if isinstance(ci_lower, (int, float)) else ci_lower,
        ci_upper=f"{ci_upper:.2f}" if isinstance(ci_upper, (int, float)) else ci_upper,
        volatility=volatility,
        forecast_status=forecast_status,
        historical_summary=historical_summary,
        recommendations=rec_str,
        question=question,
    )
