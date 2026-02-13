import numpy as np


class EscalationDetector:
    """
    Detects anomaly streak escalation over time.
    """

    def __init__(self, anomaly_scores_by_snapshot):
        self.data = anomaly_scores_by_snapshot

    def compute(self):

        results = {}

        for edge, scores in self.data.items():
            if not scores:
                continue

            consecutive = 0

            for score in scores[::-1]:
                if score > 0:
                    consecutive += 1
                else:
                    break

            if len(scores) >= 2:
                slope = np.polyfit(range(len(scores)), scores, 1)[0]
            else:
                slope = 0.0

            density = sum(
                1 for s in scores[-5:] if s > 0
            ) / min(5, len(scores))

            escalation_index = (
                0.4 * (consecutive / max(1, len(scores))) +
                0.3 * max(0, slope) +
                0.3 * density
            )

            escalation_index = float(
                max(0.0, min(1.0, escalation_index))
            )

            results[edge] = escalation_index

        return results


# --------------------------------------------------
# NEW: RISK-BASED HEALTH ESCALATION ENGINE
# --------------------------------------------------

class RiskEscalationEngine:
    """
    Applies predictive risk override to architecture health score.
    """

    CRITICAL_PENALTY = 15
    HIGH_PENALTY = 8
    MODERATE_PENALTY = 3
    MAX_TOTAL_PENALTY = 30

    def __init__(self, base_health, edge_predictions, health_trend):
        self.base_health = base_health
        self.edge_predictions = edge_predictions
        self.health_trend = health_trend

    def apply(self):

        penalty = 0
        critical_count = 0
        high_count = 0
        moderate_count = 0

        probabilities = []

        for edge in self.edge_predictions:

            tier = edge["risk_tier"]
            prob = edge["instability_probability"]
            probabilities.append(prob)

            if tier == "critical":
                penalty += self.CRITICAL_PENALTY
                critical_count += 1

            elif tier == "high":
                penalty += self.HIGH_PENALTY
                high_count += 1

            elif tier == "moderate":
                penalty += self.MODERATE_PENALTY
                moderate_count += 1

        penalty = min(penalty, self.MAX_TOTAL_PENALTY)

        avg_prob = (
            sum(probabilities) / len(probabilities)
            if probabilities else 0
        )

        if (
            self.health_trend.get("direction") == "degrading"
            and avg_prob > 0.4
        ):
            penalty += 5

        adjusted_health = max(0, self.base_health - penalty)

        return {
            "base_health": self.base_health,
            "adjusted_health": adjusted_health,
            "penalty_applied": penalty,
            "critical_edges": critical_count,
            "high_edges": high_count,
            "moderate_edges": moderate_count,
        }
