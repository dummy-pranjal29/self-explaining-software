# ses_intelligence/narrative/refiner.py


class ExecutiveNarrativeRefiner:
    """
    Converts structured ML intelligence output
    into executive-level architectural summary.
    """

    def __init__(self, intelligence_output):
        self.data = intelligence_output

    # --------------------------------------------------

    def _health_section(self):

        health = self.data.get("architecture_health", {})
        trend = self.data.get("health_trend", {})
        forecast = self.data.get("health_forecast", {})
        confidence = self.data.get("forecast_confidence", {})

        score = health.get("architecture_health_score", 0)
        direction = trend.get("direction", "stable")
        volatility = confidence.get("volatility", "unknown")
        trend_signal = forecast.get("trend_signal", "stable")

        return (
            f"The current architecture health score stands at {round(score,2)}. "
            f"Trend analysis indicates the system is {direction}. "
            f"Short-term forecasting classifies trajectory as '{trend_signal}'. "
            f"Statistical volatility is assessed as {volatility}."
        )

    # --------------------------------------------------

    def _risk_section(self):

        degradation = self.data.get(
            "early_degradation_prediction", {}
        )

        probability = degradation.get(
            "degradation_probability", None
        )

        signal = degradation.get(
            "degradation_signal", "unknown"
        )

        if probability is None:
            return "Insufficient data available to assess early degradation risk."

        return (
            f"Predictive modeling estimates a {round(probability*100,1)}% "
            f"probability of architectural degradation in the near term, "
            f"classified as '{signal}'."
        )

    # --------------------------------------------------

    def _impact_section(self):

        impact = self.data.get("edge_impact_ranking", [])

        if not impact:
            return "No structurally significant unstable edges detected."

        top = impact[0]

        return (
            f"The most structurally impactful edge is "
            f"{top['edge']} with an impact score of "
            f"{top['impact_score']}."
        )

    # --------------------------------------------------

    def _anomaly_section(self):

        anomaly_count = self.data.get("anomalies_detected", 0)

        if anomaly_count == 0:
            return "No anomalous execution patterns were detected."

        return (
            f"{anomaly_count} anomalous behavioral patterns "
            f"were identified during runtime analysis."
        )

    # --------------------------------------------------

    def generate(self):

        sections = [
            self._health_section(),
            self._risk_section(),
            self._impact_section(),
            self._anomaly_section(),
        ]

        return " ".join(sections)
