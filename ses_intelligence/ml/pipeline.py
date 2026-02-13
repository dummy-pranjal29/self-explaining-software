# ses_intelligence/ml/pipeline.py

import networkx as nx
from collections import defaultdict

from ses_intelligence.ml.features import FeatureExtractor
from ses_intelligence.ml.anomaly import AnomalyDetector
from ses_intelligence.behavior_change.history import SnapshotStore
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.history import ArchitectureHealthHistory
from ses_intelligence.architecture_health.trend import ArchitectureHealthTrend
from ses_intelligence.architecture_health.forecasting import RiskForecaster
from ses_intelligence.architecture_health.risk_labels import RiskLabelGenerator


class IntelligencePipeline:

    def __init__(self, contamination=0.4):
        self.contamination = contamination

    # --------------------------------------------------
    # SNAPSHOT RECONSTRUCTION
    # --------------------------------------------------

    def _reconstruct_snapshots(self, raw_snapshots):

        reconstructed = []

        for record in raw_snapshots:

            class ReconstructedSnapshot:
                def __init__(self, data):

                    self.edge_signature = {
                        tuple(edge.split("|")): meta
                        for edge, meta in data["edge_signature"].items()
                    }

                    self.graph = nx.DiGraph()

                    for (u, v), meta in self.edge_signature.items():
                        self.graph.add_edge(
                            u,
                            v,
                            call_count=meta["call_count"],
                            avg_duration=meta["avg_duration"],
                        )

            reconstructed.append(ReconstructedSnapshot(record))

        return reconstructed

    # --------------------------------------------------
    # MAIN INTELLIGENCE EXECUTION
    # --------------------------------------------------

    def run_intelligence(self):

        raw_snapshots = SnapshotStore.load_all()

        if not raw_snapshots or len(raw_snapshots) < 3:
            return {
                "status": "insufficient_data",
                "message": "Need at least 3 snapshots for intelligence",
            }

        snapshots = self._reconstruct_snapshots(raw_snapshots)

        # ---------------------------------
        # FEATURE EXTRACTION
        # ---------------------------------

        extractor = FeatureExtractor(snapshots)
        feature_matrix = extractor.build_feature_matrix()
        edge_features = feature_matrix["edges"]

        if not edge_features:
            return {
                "status": "no_edges",
                "message": "No edges to analyze",
            }

        # ---------------------------------
        # ANOMALY DETECTION
        # ---------------------------------

        detector = AnomalyDetector(contamination=self.contamination)
        detector.fit(edge_features)
        anomaly_results = detector.score(edge_features)

        # ---------------------------------
        # BUILD ANOMALY FREQUENCY MAP
        # ---------------------------------

        anomaly_frequency_map = defaultdict(int)

        for result in anomaly_results:
            edge_tuple = (
                result["edge"]["caller"],
                result["edge"]["callee"],
            )

            if result["is_anomaly"]:
                anomaly_frequency_map[edge_tuple] += 1

        total_edges = len(edge_features)

        for edge in anomaly_frequency_map:
            anomaly_frequency_map[edge] /= max(1, total_edges)

        # ---------------------------------
        # ARCHITECTURE HEALTH
        # ---------------------------------

        health_engine = ArchitectureHealthEngine(
            snapshots=snapshots,
            edge_features=edge_features,
            anomaly_frequency_map=anomaly_frequency_map,
        )

        health_output = health_engine.compute()

        # ---------------------------------
        # PERSIST HEALTH HISTORY
        # ---------------------------------

        history_store = ArchitectureHealthHistory()
        history_store.append(health_output)

        history_data = history_store.load()

        # ---------------------------------
        # COMPUTE TREND
        # ---------------------------------

        trend_engine = ArchitectureHealthTrend(history_data)
        trend_output = trend_engine.compute()

        # ---------------------------------
        # RISK FORECASTING (FIXED)
        # ---------------------------------

        risk_output = self._compute_edge_risk(raw_snapshots)

        # ---------------------------------
        # FINAL OUTPUT
        # ---------------------------------

        return {
            "status": "success",
            "total_edges": len(edge_features),
            "anomalies_detected": sum(
                1 for r in anomaly_results if r["is_anomaly"]
            ),
            "anomalies": anomaly_results,
            "architecture_health": health_output,
            "health_trend": trend_output,
            "edge_risk_forecast": risk_output,
        }

    # --------------------------------------------------
    # EDGE RISK FORECASTING (PROPER FORECAST)
    # --------------------------------------------------

    def _compute_edge_risk(self, raw_snapshots):

        if len(raw_snapshots) < 5:
            return {
                "status": "insufficient_snapshot_history"
            }

        # ---------------------------------
        # TRAIN ON HISTORICAL TRANSITIONS
        # ---------------------------------

        label_generator = RiskLabelGenerator(raw_snapshots)
        dataset = label_generator.generate()

        features = dataset["features"]
        labels = dataset["labels"]

        forecaster = RiskForecaster()
        training_result = forecaster.train(features, labels)

        if training_result.get("status") != "trained":
            return training_result

        # ---------------------------------
        # BUILD FEATURE MATRIX FOR LATEST SNAPSHOT ONLY
        # ---------------------------------

        latest_snapshot = raw_snapshots[-1]
        latest_edges = latest_snapshot.get("edge_signature", {})

        latest_feature_vectors = []
        edge_keys = []

        for edge_key, edge_data in latest_edges.items():

            latest_feature_vectors.append([
                edge_data.get("call_count", 0),
                edge_data.get("avg_duration", 0),
            ])

            edge_keys.append(edge_key)

        # ---------------------------------
        # PREDICT ON CURRENT ARCHITECTURE
        # ---------------------------------

        prediction_result = forecaster.predict(latest_feature_vectors)

        probabilities = prediction_result.get("probabilities", [])

        risk_classification = []

        for i, prob in enumerate(probabilities):
            risk_classification.append({
                "edge": edge_keys[i],
                "instability_probability": round(prob, 4),
                "risk_tier": forecaster.classify_risk(prob),
            })

        insights = forecaster.get_model_insights()

        return {
            "training": training_result,
            "current_edge_predictions": risk_classification,
            "model_insights": insights,
        }
