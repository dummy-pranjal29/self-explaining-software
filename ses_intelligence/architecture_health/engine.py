import os
import json
from datetime import datetime
from typing import Dict, List

from .stability_index import EdgeStabilityCalculator
from .health_score import ArchitectureHealthScore
from .confidence import ForecastConfidenceEngine


HEALTH_HISTORY_PATH = (
    "behavior_data/architecture_health/health_history.json"
)


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

    # --------------------------------------
    # Health History Persistence
    # --------------------------------------

    def _load_health_history(self) -> List[Dict]:
        if not os.path.exists(HEALTH_HISTORY_PATH):
            return []

        with open(HEALTH_HISTORY_PATH, "r") as f:
            return json.load(f)

    def _save_health_history(self, history: List[Dict]) -> None:
        os.makedirs(
            os.path.dirname(HEALTH_HISTORY_PATH),
            exist_ok=True
        )

        with open(HEALTH_HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=4)

    def _append_health_snapshot(self, health_score: float) -> None:
        history = self._load_health_history()

        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": health_score
        })

        self._save_health_history(history)

    # --------------------------------------
    # Main Execution
    # --------------------------------------

    def compute(self) -> Dict:
        if not self.snapshots:
            return {
                "status": "no_snapshots"
            }

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

        # Persist score to history
        self._append_health_snapshot(architecture_health_score)

        # -----------------------------
        # Step 3 — Statistical Confidence Modeling
        # -----------------------------
        confidence_engine = ForecastConfidenceEngine(
            history_path=HEALTH_HISTORY_PATH,
            window_size=10,
        )

        confidence_output = confidence_engine.run()

        # -----------------------------
        # Final Response
        # -----------------------------
        return {
            "status": "success",

            # Core health metrics
            "architecture_health_score": architecture_health_score,
            "edge_count": health_summary["edge_count"],

            # Stability details
            "edges": stability_rows,

            # Statistical forecast intelligence
            "forecast_intelligence": confidence_output,
        }
