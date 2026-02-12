# ses_intelligence/ml/anomaly.py

import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    def __init__(self, contamination=0.1, random_state=42):
        """
        contamination: expected anomaly ratio
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
        )
        self.fitted = False

    def _vectorize_edge_features(self, edge_features):
        """
        Convert feature dicts into numeric matrix
        """
        vectors = []
        edges = []

        for feature in edge_features:
            edges.append(feature["edge"])

            vector = [
                feature["call_count_latest"],
                feature["avg_duration_latest"],
                feature["timing_slope"],
                feature["timing_volatility"],
                feature["appearance_frequency"],
                feature["age_in_snapshots"],
                feature["drift_score"],
                feature["regression_frequency"],
            ]

            vectors.append(vector)

        return np.array(vectors), edges

    def fit(self, edge_features):
        X, _ = self._vectorize_edge_features(edge_features)
        if len(X) > 0:
            self.model.fit(X)
            self.fitted = True

    def score(self, edge_features):
        if not self.fitted:
            raise RuntimeError("Model must be fitted before scoring")

        X, edges = self._vectorize_edge_features(edge_features)

        anomaly_labels = self.model.predict(X)
        anomaly_scores = self.model.decision_function(X)

        results = []

        for i in range(len(edges)):
            results.append(
                {
                    "edge": {
                        "caller": edges[i][0],
                        "callee": edges[i][1],
                    },
                    "is_anomaly": bool(anomaly_labels[i] == -1),
                    "anomaly_score": float(anomaly_scores[i]),
                }
            )


        return results
