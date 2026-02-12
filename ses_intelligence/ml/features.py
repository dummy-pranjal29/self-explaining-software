# -*- coding: utf-8 -*-


import numpy as np
import networkx as nx
from collections import defaultdict


class FeatureExtractor:
    def __init__(self, snapshots):
        """
        snapshots: List[BehaviorSnapshot]
        Must be ordered oldest to newest
        """
        self.snapshots = snapshots
        self.total_snapshots = len(snapshots)

    # ---------------------------
    # EDGE FEATURE EXTRACTION
    # ---------------------------

    def extract_edge_features(self):
        edge_history = defaultdict(list)

        # Collect edge history
        for index, snapshot in enumerate(self.snapshots):
            for (u, v), data in snapshot.edge_signature.items():
                edge_history[(u, v)].append(
                    {
                        "snapshot_index": index,
                        "call_count": data["call_count"],
                        "avg_duration": data["avg_duration"],
                    }
                )

        features = []

        for edge, history in edge_history.items():
            durations = [h["avg_duration"] for h in history]
            call_counts = [h["call_count"] for h in history]

            first = history[0]
            latest = history[-1]

            # Linear slope
            x = np.arange(len(durations))
            if len(durations) > 1:
                slope = np.polyfit(x, durations, 1)[0]
            else:
                slope = 0.0

            volatility = float(np.std(durations))

            appearance_frequency = len(history) / self.total_snapshots

            age_in_snapshots = self.total_snapshots - first["snapshot_index"]

            drift_score = 0.0
            if first["avg_duration"] != 0:
                drift_score = abs(
                    (latest["avg_duration"] - first["avg_duration"])
                    / first["avg_duration"]
                )

            regression_frequency = sum(
                1
                for i in range(1, len(durations))
                if durations[i] > durations[i - 1]
            )

            features.append(
                {
                    "edge": edge,
                    "call_count_latest": latest["call_count"],
                    "avg_duration_latest": latest["avg_duration"],
                    "timing_slope": slope,
                    "timing_volatility": volatility,
                    "appearance_frequency": appearance_frequency,
                    "age_in_snapshots": age_in_snapshots,
                    "drift_score": drift_score,
                    "regression_frequency": regression_frequency,
                }
            )

        return features

    # ---------------------------
    # NODE FEATURE EXTRACTION
    # ---------------------------

    def extract_node_features(self):
        if not self.snapshots:
            return []

        latest_snapshot = self.snapshots[-1]
        first_snapshot = self.snapshots[0]

        G_latest = latest_snapshot.graph
        G_first = first_snapshot.graph

        centrality = nx.degree_centrality(G_latest)

        features = []

        for node in G_latest.nodes():
            fan_in_latest = G_latest.in_degree(node)
            fan_out_latest = G_latest.out_degree(node)

            fan_in_first = G_first.in_degree(node) if node in G_first else 0
            fan_out_first = G_first.out_degree(node) if node in G_first else 0

            # Entropy of outgoing calls
            total_calls = 0
            outgoing_calls = []

            for _, v, data in G_latest.out_edges(node, data=True):
                total_calls += data.get("call_count", 0)
                outgoing_calls.append(data.get("call_count", 0))

            entropy = 0.0
            if total_calls > 0:
                for count in outgoing_calls:
                    p = count / total_calls
                    entropy -= p * np.log(p)

            dominance_ratio = fan_out_latest / (fan_in_latest + 1)

            features.append(
                {
                    "node": node,
                    "fan_in": fan_in_latest,
                    "fan_out": fan_out_latest,
                    "fan_in_growth": fan_in_latest - fan_in_first,
                    "fan_out_growth": fan_out_latest - fan_out_first,
                    "centrality_score": centrality.get(node, 0.0),
                    "dominance_ratio": dominance_ratio,
                    "entropy_contribution": entropy,
                }
            )

        return features

    # ---------------------------
    # FULL MATRIX
    # ---------------------------

    def build_feature_matrix(self):
        return {
            "edges": self.extract_edge_features(),
            "nodes": [],
        }
