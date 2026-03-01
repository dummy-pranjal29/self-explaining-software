from typing import Dict, List, Optional

from .stability_index import EdgeStabilityCalculator
from .health_score import ArchitectureHealthScore
from .confidence import ForecastConfidenceEngine
from .history import ArchitectureHealthHistory


class ArchitectureHealthEngine:
    """
    Full architecture health orchestration engine.

    Responsibilities:
    - Edge stability computation
    - Architecture health scoring
    - Health history persistence
    - Statistical forecast confidence modeling
    
    Supports multi-project isolation via project_id.
    """

    def __init__(
        self,
        snapshots,
        edge_features,
        anomaly_frequency_map=None,
        project_id: Optional[str] = None,
    ):
        """
        Initialize the architecture health engine.
        
        Args:
            snapshots: List of behavior snapshots
            edge_features: Edge feature matrix from FeatureExtractor
            anomaly_frequency_map: Optional map of anomaly frequencies
            project_id: Optional project identifier for multi-project isolation
        """
        self.snapshots = snapshots
        self.edge_features = edge_features
        self.anomaly_frequency_map = anomaly_frequency_map or {}
        self.project_id = project_id or "default"

        self.history_store = ArchitectureHealthHistory(project_id=self.project_id)

    # --------------------------------------
    # Main Execution
    # --------------------------------------

    def compute(self) -> Dict:
        # Fallback defaults
        fallback = {
            "overall_score": 100.0,
            "status": "insufficient_data",
            "confidence": 0.0
        }

        if not self.snapshots:
            return fallback

        latest_snapshot = self.snapshots[-1]
        graph = getattr(latest_snapshot, "graph", None)
        if graph is None:
            return fallback

        # Step 1 — Edge Stability
        try:
            stability_calc = EdgeStabilityCalculator(
                self.edge_features,
                self.anomaly_frequency_map,
            )
            stability_rows = stability_calc.compute()
        except Exception:
            stability_rows = []

        # Step 2 — Architecture Score
        try:
            health_calc = ArchitectureHealthScore(
                graph,
                stability_rows,
                self.edge_features,
            )
            health_summary = health_calc.compute()
            architecture_health_score = health_summary.get("architecture_health_score", 100.0)
            edge_count = health_summary.get("edge_count", 0)
        except Exception:
            architecture_health_score = 100.0
            edge_count = 0

        # Derived Metrics
        avg_stability = 0.0
        if stability_rows:
            try:
                total_stability = sum(row.get("stability_index", 0) for row in stability_rows)
                avg_stability = total_stability / len(stability_rows)
            except Exception:
                avg_stability = 0.0
        anomaly_count = sum(1 for row in stability_rows if row.get("anomaly_flag") is True) if stability_rows else 0
        drift_score = 1 - avg_stability if avg_stability else 0.0

        # Step 3 — Persist To History
        enriched_health_output = {
            "health_score": architecture_health_score,
            "architecture_health_score": architecture_health_score,
            "stability_index": avg_stability,
            "drift_score": drift_score,
            "anomaly_count": anomaly_count,
            "edge_count": edge_count,
            "edges": stability_rows,
            "project_id": self.project_id,
        }
        try:
            self.history_store.append(enriched_health_output)
        except Exception:
            pass

        # Step 4 — Forecast Intelligence
        try:
            confidence_engine = ForecastConfidenceEngine(
                history_path=str(self.history_store.path),
                window_size=10,
            )
            confidence_output = confidence_engine.run()
            confidence = float(confidence_output.get("confidence", 0.0))
        except Exception:
            confidence_output = {}
            confidence = 0.0

        # Health Status Label
        if architecture_health_score >= 80:
            health_label = "Stable"
        elif architecture_health_score >= 60:
            health_label = "Moderate"
        elif architecture_health_score >= 40:
            health_label = "Degrading"
        else:
            health_label = "Critical"

        # Trend Direction
        trend_direction = confidence_output.get("trend", "flat")
        if isinstance(trend_direction, (int, float)):
            if trend_direction > 2:
                trend_direction = "improving"
            elif trend_direction > 0:
                trend_direction = "slightly_improving"
            elif trend_direction == 0:
                trend_direction = "flat"
            elif trend_direction > -2:
                trend_direction = "slightly_declining"
            else:
                trend_direction = "declining"

        volatility_label = confidence_output.get("volatility", "medium")

        # Top Risk Drivers
        top_risk_drivers = []
        if stability_rows:
            try:
                sorted_edges = sorted(
                    stability_rows,
                    key=lambda x: (
                        0 if x.get("anomaly_flag") else 1,
                        x.get("stability_index", 1)
                    )
                )
                for edge in sorted_edges[:2]:
                    if edge.get("anomaly_flag") or edge.get("stability_index", 1) < 0.8:
                        driver = {
                            "edge": f"{edge.get('source', '?')} → {edge.get('target', '?')}",
                            "stability": edge.get("stability_index", 0),
                            "anomaly": edge.get("anomaly_flag", False)
                        }
                        top_risk_drivers.append(driver)
            except Exception:
                top_risk_drivers = []

        # Delta from last snapshot
        delta = 0
        try:
            history = self.history_store.get_history()
            if len(history) >= 2:
                last_score = history[-1].get("architecture_health_score", 0)
                prev_score = history[-2].get("architecture_health_score", 0)
                delta = last_score - prev_score
        except Exception:
            delta = 0

        # Final Output (always includes overall_score, status, confidence)
        output = {
            "overall_score": float(architecture_health_score),
            "status": "success" if architecture_health_score < 100.0 else "insufficient_data",
            "confidence": confidence,
            "project_id": self.project_id,
            "architecture_health_score": architecture_health_score,
            "health_score": architecture_health_score,
            "edge_count": edge_count,
            "health_label": health_label,
            "risk_label": health_label.upper(),
            "trend_direction": trend_direction,
            "volatility_label": volatility_label,
            "delta": delta,
            "top_risk_drivers": top_risk_drivers,
            "stability_index": avg_stability,
            "drift_score": drift_score,
            "anomaly_count": anomaly_count,
            "edges": stability_rows,
            "forecast_intelligence": confidence_output,
        }
        return output
