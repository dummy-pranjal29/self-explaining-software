# ses_intelligence/narrative/drivers.py

def analyze_risk_edges(risk_data: dict) -> list:
    """
    Expected risk_data format:
    {
        "high_risk_edges": [
            {
                "edge": "signup -> save_user",
                "risk_probability": 0.82,
                "instability_score": 0.41,
                "variance_increase": 0.34
            }
        ]
    }
    """

    results = []

    high_risk_edges = risk_data.get("high_risk_edges", [])

    for edge_data in high_risk_edges:
        edge = edge_data.get("edge")
        risk_probability = edge_data.get("risk_probability", 0)
        instability = edge_data.get("instability_score", 0)
        variance = edge_data.get("variance_increase", 0)

        explanation = (
            f"Invocation variance increased by {round(variance * 100, 2)}% "
            f"with instability score {round(instability, 2)}."
        )

        results.append({
            "edge": edge,
            "risk_probability": round(risk_probability, 2),
            "instability_score": round(instability, 2),
            "explanation": explanation
        })

    return results
