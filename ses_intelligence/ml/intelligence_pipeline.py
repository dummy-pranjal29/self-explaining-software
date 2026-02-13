# ses_intelligence/ml/intelligence_pipeline.py

import json
from collections import defaultdict

from ses_intelligence.ml.anomaly import AnomalyDetector
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine


class RuntimeIntelligencePipeline:
    """
    Orchestrates:
    - Feature extraction (already done externally)
    - IsolationForest anomaly detection
    - Architecture Health computation
    """

    def __init__(self, contamination=0.1):
        self.anomaly_detector = AnomalyDetector(contamination=contamination)

    # -----------------------------------------
    # MAIN EXECUTION
    # -----------------------------------------

    def run(self, snapshots, edge_features):
        """
        snapshots: List[BehaviorSnapshot]
        edge_features: output from FeatureExtractor.extract_edge_features()
        """

        if not edge_features:
            return {}

        # -------------------------
        # 1️⃣ FIT + SCORE ANOMALY
        # -------------------------

        self.anomaly_detector.fit(edge_features)
        anomaly_results = self.anomaly_detector.score(edge_features)

        # -------------------------
        # 2️⃣ BUILD ANOMALY FREQUENCY MAP
        # -------------------------

        anomaly_frequency_map = defaultdict(int)

        for result in anomaly_results:
            edge_tuple = (
                result["edge"]["caller"],
                result["edge"]["callee"],
            )

            if result["is_anomaly"]:
                anomaly_frequency_map[edge_tuple] += 1

        total_edges = len(edge_features)

        # convert counts → frequency
        for edge in anomaly_frequency_map:
            anomaly_frequency_map[edge] /= max(1, total_edges)

        # -------------------------
        # 3️⃣ ARCHITECTURE HEALTH
        # -------------------------

        health_engine = ArchitectureHealthEngine(
            snapshots=snapshots,
            edge_features=edge_features,
            anomaly_frequency_map=anomaly_frequency_map,
        )

        health_output = health_engine.compute()

        # -------------------------
        # FINAL STRUCTURED OUTPUT
        # -------------------------

        return {
            "anomalies": anomaly_results,
            "architecture_health": health_output,
        }

    # -----------------------------------------
    # OPTIONAL JSON PERSISTENCE
    # -----------------------------------------

    def persist(self, output, path="runtime_intelligence.json"):
        with open(path, "w") as f:
            json.dump(output, f, indent=2, default=str)
