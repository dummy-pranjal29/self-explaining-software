import json
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError
from ses_intelligence.architecture_health.history import (
    ArchitectureHealthHistory
)

# ==========================================================
# EDGE-LEVEL RISK FORECASTER
# ==========================================================

MIN_TRAINING_SAMPLES = 10
MIN_CLASS_VARIETY = 2


class RiskForecaster:
    """
    Edge-level future instability predictor.
    """

    def __init__(self):
        self.model = LogisticRegression(
            solver="liblinear",
            max_iter=200,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.trained = False
        self.class_balance_warning = False

    # --------------------------------------------------
    # Training
    # --------------------------------------------------

    def train(self, feature_matrix, labels):

        if feature_matrix is None or labels is None:
            self.trained = False
            return {
                "status": "invalid_input",
                "message": "Feature matrix or labels are None."
            }

        if len(feature_matrix) < MIN_TRAINING_SAMPLES:
            self.trained = False
            return {
                "status": "insufficient_data",
                "message": f"Need at least {MIN_TRAINING_SAMPLES} samples."
            }

        if len(feature_matrix) != len(labels):
            self.trained = False
            return {
                "status": "dimension_mismatch",
                "message": "Features and labels length mismatch."
            }

        unique_classes = set(labels)

        if len(unique_classes) < MIN_CLASS_VARIETY:
            self.trained = False
            self.class_balance_warning = True
            return {
                "status": "single_class_detected",
                "message": "Training labels contain only one class."
            }

        try:
            X = np.array(feature_matrix)
            y = np.array(labels)

            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)

            self.trained = True
            self.class_balance_warning = False

            return {
                "status": "trained",
                "samples": len(feature_matrix),
                "positive_ratio": float(np.mean(y))
            }

        except Exception as e:
            self.trained = False
            return {
                "status": "training_failed",
                "message": str(e)
            }

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    def predict(self, feature_matrix):

        if not self.trained:
            return {
                "status": "model_not_trained",
                "probabilities": [0.0 for _ in feature_matrix]
            }

        try:
            X = np.array(feature_matrix)
            X_scaled = self.scaler.transform(X)
            probs = self.model.predict_proba(X_scaled)

            return {
                "status": "prediction_generated",
                "probabilities": [float(p[1]) for p in probs]
            }

        except NotFittedError:
            return {
                "status": "model_not_fitted_error",
                "probabilities": [0.0 for _ in feature_matrix]
            }

    # --------------------------------------------------
    # Explainability
    # --------------------------------------------------

    def get_model_insights(self):

        if not self.trained:
            return {
                "status": "model_not_trained"
            }

        coefficients = self.model.coef_[0]
        intercept = self.model.intercept_[0]

        return {
            "status": "insights_available",
            "coefficients": [float(c) for c in coefficients],
            "intercept": float(intercept),
            "class_balance_warning": self.class_balance_warning
        }

    # --------------------------------------------------
    # Risk Tier Classification
    # --------------------------------------------------

    @staticmethod
    def classify_risk(probability):

        if probability >= 0.75:
            return "critical"
        elif probability >= 0.50:
            return "high"
        elif probability >= 0.25:
            return "moderate"
        else:
            return "low"


# ==========================================================
# ADVANCED ARCHITECTURE HEALTH FORECASTER (PHASE 3)
# ==========================================================

class ArchitectureHealthForecaster:
    """
    Advanced architecture health forecasting with:

    - Long-term slope
    - Short-term slope
    - Exponential smoothing
    - Divergence detection
    """

    MIN_POINTS_REQUIRED = 5
    RISK_THRESHOLD = 70

    def __init__(self, alpha=0.4, short_window=10):
        self.alpha = alpha
        self.short_window = short_window
        self.history = ArchitectureHealthHistory().load()

    # --------------------------------------------------

    def _extract_scores(self):

        scores = []

        for entry in self.history:

            try:
                health_block = entry.get("health", {})
                score = health_block.get("architecture_health_score")

                if score is not None:
                    scores.append(float(score))

            except (KeyError, TypeError):
                continue

        return scores

    # --------------------------------------------------

    def _compute_slope(self, values):

        if len(values) < 2:
            return 0.0

        t = np.arange(len(values))
        slope = np.polyfit(t, values, 1)[0]

        return slope

    # --------------------------------------------------

    def _exponential_smoothing(self, values):

        smoothed = values[0]

        for v in values[1:]:
            smoothed = self.alpha * v + (1 - self.alpha) * smoothed

        return smoothed

    # --------------------------------------------------

    def forecast(self, steps_ahead=10):

        scores = self._extract_scores()

        if len(scores) < self.MIN_POINTS_REQUIRED:
            return {
                "status": "insufficient_data",
                "message": "Not enough history for forecasting"
            }

        current_health = scores[-1]

        # Long-term slope
        long_term_slope = self._compute_slope(scores)

        # Short-term slope
        recent = (
            scores[-self.short_window:]
            if len(scores) >= self.short_window
            else scores
        )

        short_term_slope = self._compute_slope(recent)

        # Linear projection
        linear_projection = (
            current_health + (long_term_slope * steps_ahead)
        )

        linear_projection = float(
            max(0, min(100, linear_projection))
        )

        # Exponential smoothing projection
        smoothed_projection = float(
            max(0, min(100, self._exponential_smoothing(scores)))
        )

        # Divergence signal
        divergence = short_term_slope - long_term_slope

        if divergence < -0.05:
            trend_signal = "early_degradation"
        elif divergence > 0.05:
            trend_signal = "accelerating_improvement"
        else:
            trend_signal = "stable"

        # Risk crossing estimate
        snapshots_until_risk = None

        if long_term_slope < 0:
            intercept = np.polyfit(
                np.arange(len(scores)),
                scores,
                1
            )[1]

            t_cross = (
                (self.RISK_THRESHOLD - intercept)
                / long_term_slope
            )

            if t_cross > len(scores):
                snapshots_until_risk = int(
                    t_cross - len(scores)
                )

        return {
            "status": "forecast_generated",
            "current_health": float(current_health),
            "long_term_slope": float(long_term_slope),
            "short_term_slope": float(short_term_slope),
            "trend_divergence": float(divergence),
            "trend_signal": trend_signal,
            "linear_projection_next_window": linear_projection,
            "smoothed_projection": smoothed_projection,
            "snapshots_until_risk": snapshots_until_risk,
        }
