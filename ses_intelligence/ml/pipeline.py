# ses_intelligence/ml/pipeline.py

from ses_intelligence.ml.features import FeatureExtractor
from ses_intelligence.ml.anomaly import AnomalyDetector
from ses_intelligence.behavior_change.history import SnapshotStore


class IntelligencePipeline:
    def __init__(self, contamination=0.4):
        self.contamination = contamination

    def _reconstruct_snapshots(self, raw_snapshots):
        """
        Convert raw JSON snapshot dicts into lightweight
        objects compatible with FeatureExtractor.
        """

        reconstructed = []

        for record in raw_snapshots:
            class ReconstructedSnapshot:
                def __init__(self, data):
                    # Convert "A|B" back into (A, B)
                    self.edge_signature = {
                        tuple(edge.split("|")): meta
                        for edge, meta in data["edge_signature"].items()
                    }

                    # Node features need graph structure
                    # We will not compute node features here yet.
                    # Set graph = None safely.
                    self.graph = None

            reconstructed.append(ReconstructedSnapshot(record))

        return reconstructed

    def run_anomaly_detection(self):
        raw_snapshots = SnapshotStore.load_all()

        if not raw_snapshots or len(raw_snapshots) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 snapshots",
            }

        snapshots = self._reconstruct_snapshots(raw_snapshots)

        extractor = FeatureExtractor(snapshots)
        feature_matrix = extractor.build_feature_matrix()
        edge_features = feature_matrix["edges"]

        if not edge_features:
            return {
                "status": "no_edges",
                "message": "No edges to analyze",
            }

        detector = AnomalyDetector(contamination=self.contamination)
        detector.fit(edge_features)
        anomaly_results = detector.score(edge_features)

        return {
            "status": "success",
            "total_edges": len(edge_features),
            "anomalies_detected": sum(
                1 for r in anomaly_results if r["is_anomaly"]
            ),
            "results": anomaly_results,
        }
