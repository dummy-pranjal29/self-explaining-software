from .stability_index import EdgeStabilityCalculator
from .health_score import ArchitectureHealthScore


class ArchitectureHealthEngine:
    """
    Orchestrates full Phase 3 health computation.
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

    def compute(self):
        if not self.snapshots:
            return {}

        latest_snapshot = self.snapshots[-1]
        graph = latest_snapshot.graph

        # Step 1: Edge Stability
        stability_calc = EdgeStabilityCalculator(
            self.edge_features,
            self.anomaly_frequency_map,
        )

        stability_rows = stability_calc.compute()

        # Step 2: Architecture Score
        health_calc = ArchitectureHealthScore(
            graph,
            stability_rows,
            self.edge_features,
        )

        health_summary = health_calc.compute()

        return {
            "architecture_health_score": health_summary[
                "architecture_health_score"
            ],
            "edge_count": health_summary["edge_count"],
            "edges": stability_rows,
        }
