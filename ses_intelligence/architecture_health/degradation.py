# ses_intelligence/architecture_health/degradation.py

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ses_intelligence.architecture_health.history import (
    ArchitectureHealthHistory
)


class EarlyDegradationClassifier:
    """
    Predicts whether architecture health is about to degrade
    based on momentum weakening rather than absolute crash.

    Degradation is defined as:
    Future slope significantly weaker than current slope.
    """

    WINDOW_SIZE = 5
    FUTURE_LOOKAHEAD = 3
    MOMENTUM_RATIO_THRESHOLD = 0.5  # future slope < 50% of current slope

    def __init__(self):
        self.history = ArchitectureHealthHistory().load()
        self.model = LogisticRegression(
            solver="liblinear",
            max_iter=200,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.trained = False

    # --------------------------------------------------

    def _extract_scores(self):

        scores = []

        for entry in self.history:
            health_block = entry.get("health", {})
            score = health_block.get("architecture_health_score")

            if score is not None:
                scores.append(float(score))

        return scores

    # --------------------------------------------------

    def _compute_slope(self, values):

        if len(values) < 2:
            return 0.0

        t = np.arange(len(values))
        slope = np.polyfit(t, values, 1)[0]

        return slope

    # --------------------------------------------------

    def _build_dataset(self, scores):

        X = []
        y = []

        for i in range(
            len(scores) - self.WINDOW_SIZE - self.FUTURE_LOOKAHEAD
        ):

            window = scores[i:i + self.WINDOW_SIZE]
            future = scores[
                i + self.WINDOW_SIZE :
                i + self.WINDOW_SIZE + self.FUTURE_LOOKAHEAD
            ]

            current_health = window[-1]

            current_slope = self._compute_slope(window)
            future_slope = self._compute_slope(future)

            # Degradation if momentum drops significantly
            if current_slope > 0:
                label = (
                    1
                    if future_slope < current_slope * self.MOMENTUM_RATIO_THRESHOLD
                    else 0
                )
            else:
                label = 0

            X.append([
                current_health,
                current_slope,
                np.std(window),
            ])

            y.append(label)

        return np.array(X), np.array(y)

    # --------------------------------------------------

    def train(self):

        scores = self._extract_scores()

        if len(scores) < 15:
            return {
                "status": "insufficient_data"
            }

        X, y = self._build_dataset(scores)

        # Need both classes for training
        if len(set(y)) < 2:
            return {
                "status": "single_class_detected"
            }

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        self.trained = True

        return {
            "status": "trained",
            "samples": len(X),
            "positive_ratio": float(np.mean(y))
        }

    # --------------------------------------------------

    def predict_current_risk(self):

        if not self.trained:
            return {
                "status": "model_not_trained"
            }

        scores = self._extract_scores()

        if len(scores) < self.WINDOW_SIZE:
            return {
                "status": "insufficient_data"
            }

        window = scores[-self.WINDOW_SIZE:]

        current_health = window[-1]
        current_slope = self._compute_slope(window)

        features = np.array([
            [current_health, current_slope, np.std(window)]
        ])

        X_scaled = self.scaler.transform(features)
        probability = self.model.predict_proba(X_scaled)[0][1]

        if probability >= 0.75:
            signal = "high_risk"
        elif probability >= 0.5:
            signal = "moderate_risk"
        else:
            signal = "stable"

        return {
            "status": "prediction_generated",
            "degradation_probability": float(probability),
            "degradation_signal": signal
        }
