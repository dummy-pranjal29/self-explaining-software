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

        if not self.snapshots:
            return {"status": "no_snapshots"}

        latest_snapshot = self.snapshots[-1]
        graph = latest_snapshot.graph

        # -----------------------------
        # Step 1 — Edge Stability
        # -----------------------------
        stability_calc = EdgeStabilityCalculator(
            self.edge_features,
            self.anomaly_frequency_map,
        )

        stability_rows = stability_calc.compute()

        # -----------------------------
        # Step 2 — Architecture Score
        # -----------------------------
        health_calc = ArchitectureHealthScore(
            graph,
            stability_rows,
            self.edge_features,
        )

        health_summary = health_calc.compute()

        architecture_health_score = health_summary[
            "architecture_health_score"
        ]

        # -----------------------------
        # Derived Metrics
        # -----------------------------

        # Average stability index
        avg_stability = 0.0
        if stability_rows:
            total_stability = sum(
                row.get("stability_index", 0)
                for row in stability_rows
            )
            avg_stability = total_stability / len(stability_rows)

        # Anomaly pressure (normalized)
        anomaly_count = sum(
            1 for row in stability_rows
            if row.get("anomaly_flag") is True
        )

        # Simple drift score proxy
        drift_score = 1 - avg_stability if avg_stability else 0.0

        # -----------------------------
        # Step 3 — Persist To History
        # -----------------------------

        enriched_health_output = {
            "health_score": architecture_health_score,
            "architecture_health_score": architecture_health_score,
            "stability_index": avg_stability,
            "drift_score": drift_score,
            "anomaly_count": anomaly_count,
            "edge_count": health_summary["edge_count"],
            "edges": stability_rows,
            "project_id": self.project_id,
        }

        self.history_store.append(enriched_health_output)

        # -----------------------------
        # Step 4 — Forecast Intelligence
        # -----------------------------

        confidence_engine = ForecastConfidenceEngine(
            history_path=str(self.history_store.path),
            window_size=10,
        )

        confidence_output = confidence_engine.run()

        # -----------------------------
        # Determine Health Status Label
        # -----------------------------
        if architecture_health_score >= 80:
            health_label = "Stable"
        elif architecture_health_score >= 60:
            health_label = "Moderate"
        elif architecture_health_score >= 40:
            health_label = "Degrading"
        else:
            health_label = "Critical"
        
        # Determine trend direction (from forecast intelligence)
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
        
        # Determine volatility label
        volatility_label = confidence_output.get("volatility", "medium")
        
        # Get top risk drivers (highest anomaly edges)
        top_risk_drivers = []
        if stability_rows:
            # Sort by anomaly flag and lowest stability
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
        
        # Calculate delta from last snapshot
        delta = 0
        try:
            history = self.history_store.get_history()
            if len(history) >= 2:
                last_score = history[-1].get("architecture_health_score", 0)
                prev_score = history[-2].get("architecture_health_score", 0)
                delta = last_score - prev_score
        except Exception:
            pass

        # -----------------------------
        # Final Engine Output
        # -----------------------------

        return {
            "status": "success",
            "project_id": self.project_id,

            # Core health metrics
            "architecture_health_score": architecture_health_score,
            "health_score": architecture_health_score,
            "edge_count": health_summary["edge_count"],

            # Health Status
            "health_label": health_label,
            "risk_label": health_label.upper(),
            
            # Trend & Volatility
            "trend_direction": trend_direction,
            "volatility_label": volatility_label,
            "delta": delta,
            
            # Top Risk Drivers
            "top_risk_drivers": top_risk_drivers,

            # Stability metrics
            "stability_index": avg_stability,
            "drift_score": drift_score,
            "anomaly_count": anomaly_count,
            "edges": stability_rows,

            # Forecast intelligence
            "forecast_intelligence": confidence_output,
        }
