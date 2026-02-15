print("NEW ARCHITECTURE HEALTH ENGINE LOADED")

from typing import Dict, List

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
    """

    def __init__(
        self,
        snapshots,
        edge_features,
        anomaly_frequency_map=None,
    ):
        self.snapshots = snapshots
        self.edge_features = edge_features
        self.anomaly_frequency_map = anomaly_frequency_map or {}

        self.history_store = ArchitectureHealthHistory()

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
        # Final Engine Output
        # -----------------------------

        return {
            "status": "success",

            # Core health metrics
            "architecture_health_score": architecture_health_score,
            "edge_count": health_summary["edge_count"],

            # Stability metrics
            "stability_index": avg_stability,
            "drift_score": drift_score,
            "anomaly_count": anomaly_count,
            "edges": stability_rows,

            # Forecast intelligence
            "forecast_intelligence": confidence_output,
        }
