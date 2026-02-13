class RiskLabelGenerator:
    """
    Generates supervised labels for edge instability
    using snapshot-to-snapshot comparison.
    """

    def __init__(self, snapshots):
        self.snapshots = snapshots

    # --------------------------------------------------

    def generate(self):

        features = []
        labels = []

        if not self.snapshots or len(self.snapshots) < 2:
            return {
                "features": [],
                "labels": []
            }

        for i in range(len(self.snapshots) - 1):

            current = self.snapshots[i]
            nxt = self.snapshots[i + 1]

            current_edges = current.get("edge_signature", {})
            next_edges = nxt.get("edge_signature", {})

            for edge_key, edge_data in current_edges.items():

                feature_vector = self._extract_features(edge_data)

                label = self._compute_label(
                    edge_key,
                    edge_data,
                    next_edges
                )

                features.append(feature_vector)
                labels.append(label)

        return {
            "features": features,
            "labels": labels
        }

    # --------------------------------------------------

    def _compute_label(self, edge_key, edge_data, next_edges):

        if edge_key not in next_edges:
            return 1  # Edge disappeared

        next_edge = next_edges[edge_key]

        current_duration = edge_data.get("avg_duration", 0)
        next_duration = next_edge.get("avg_duration", 0)

        if next_duration > current_duration * 1.3:
            return 1  # Timing regression

        return 0

    # --------------------------------------------------

    def _extract_features(self, edge_data):

        return [
            edge_data.get("call_count", 0),
            edge_data.get("avg_duration", 0),
        ]
