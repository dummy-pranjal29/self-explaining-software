# ses_intelligence/architecture_health/stability_index.py


class EdgeStabilityCalculator:
    """
    Computes deterministic Edge Stability Index (ESI)
    using absolute bounded scaling instead of cross-edge normalization.

    This avoids exaggerated instability when edge count is small.
    """

    def __init__(self, edge_features, anomaly_flags=None):
        """
        edge_features: list of feature dicts from FeatureExtractor
        anomaly_flags: dict {(u, v): anomaly_frequency}
        """
        self.edge_features = edge_features
        self.anomaly_flags = anomaly_flags or {}

    # --------------------------------------------------
    # SCALING FUNCTIONS
    # --------------------------------------------------

    @staticmethod
    def _volatility_to_stability(volatility):
        """
        Convert timing volatility into a stability score.
        Smoothly decays as volatility increases.
        Bounded in (0, 1].
        """
        return 1 / (1 + volatility)

    @staticmethod
    def _slope_to_stability(slope):
        """
        Convert timing slope magnitude into stability score.
        Penalizes monotonic drift.
        """
        return 1 / (1 + abs(slope))

    # --------------------------------------------------
    # MAIN COMPUTE
    # --------------------------------------------------

    def compute(self):
        if not self.edge_features:
            return []

        results = []

        for row in self.edge_features:
            edge = row["edge"]

            # Structural consistency
            scs = row["appearance_frequency"]

            # Temporal stability (volatility-based)
            tss = self._volatility_to_stability(
                row["timing_volatility"]
            )

            # Drift stability (slope-based)
            dss = self._slope_to_stability(
                row["timing_slope"]
            )

            # Anomaly pressure
            anomaly_freq = self.anomaly_flags.get(edge, 0.0)
            aps = 1 - anomaly_freq

            # Weighted stability index
            esi = (
                0.30 * scs +
                0.25 * tss +
                0.20 * dss +
                0.25 * aps
            )

            # Clamp to [0,1]
            esi = float(max(0.0, min(1.0, esi)))

            results.append(
                {
                    "edge": edge,
                    "stability_index": esi,
                    "components": {
                        "structural_consistency": scs,
                        "temporal_stability": tss,
                        "drift_stability": dss,
                        "anomaly_pressure": aps,
                    },
                }
            )

        return results
