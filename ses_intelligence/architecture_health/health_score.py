import numpy as np
import networkx as nx


class ArchitectureHealthScore:
    """
    Aggregates Edge Stability Indices into a system score.
    """

    def __init__(self, graph: nx.DiGraph, stability_rows, edge_features):
        self.graph = graph
        self.stability_rows = stability_rows
        self.feature_map = {
            row["edge"]: row for row in edge_features
        }

    @staticmethod
    def _normalize(values):
        if not values:
            return []

        arr = np.array(values, dtype=float)
        min_v = np.min(arr)
        max_v = np.max(arr)

        if max_v - min_v == 0:
            return [0.5 for _ in arr]

        return list((arr - min_v) / (max_v - min_v))

    def compute(self):
        if not self.stability_rows:
            return {
                "architecture_health_score": 100.0,
                "edge_count": 0,
            }

        centrality = nx.betweenness_centrality(self.graph)

        call_counts = []
        ages = []
        centralities = []

        for row in self.stability_rows:
            edge = row["edge"]
            features = self.feature_map.get(edge, {})

            call_counts.append(features.get("call_count_latest", 0))
            ages.append(features.get("age_in_snapshots", 1))

            u, v = edge
            centralities.append(
                centrality.get(u, 0.0) + centrality.get(v, 0.0)
            )

        norm_call = self._normalize(call_counts)
        norm_age = self._normalize(ages)
        norm_central = self._normalize(centralities)

        weighted_scores = []
        weights = []

        for i, row in enumerate(self.stability_rows):
            weight = (
                0.5 * norm_call[i] +
                0.3 * norm_age[i] +
                0.2 * norm_central[i]
            )

            weighted_scores.append(
                row["stability_index"] * weight
            )
            weights.append(weight)

        if sum(weights) == 0:
            return {
                "architecture_health_score": 100.0,
                "edge_count": len(self.stability_rows),
            }

        final_score = sum(weighted_scores) / sum(weights)

        return {
            "architecture_health_score": round(final_score * 100, 2),
            "edge_count": len(self.stability_rows),
        }
