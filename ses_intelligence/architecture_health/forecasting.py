import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError


MIN_TRAINING_SAMPLES = 10
MIN_CLASS_VARIETY = 2


class RiskForecaster:
    """
    Edge-level future instability predictor.

    Uses Logistic Regression for probabilistic prediction
    of instability in future snapshots.

    Designed for:
    - Small datasets
    - Deterministic fallback
    - Explainable coefficients
    - Stable behavior
    """

    def __init__(self):
        self.model = LogisticRegression(
            solver="liblinear",  # better for small datasets
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
        """
        feature_matrix: List[List[float]]
        labels: List[int]  (0 = stable, 1 = future instability)
        """

        # -----------------------------------------
        # Basic validation
        # -----------------------------------------

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

        # -----------------------------------------
        # Training
        # -----------------------------------------

        try:
            X = np.array(feature_matrix)
            y = np.array(labels)

            # Normalize features
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
        """
        Returns instability probabilities.
        """

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
        """
        Returns model coefficients for explainability.
        """

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
        """
        Converts probability into risk tier.
        """

        if probability >= 0.75:
            return "critical"
        elif probability >= 0.50:
            return "high"
        elif probability >= 0.25:
            return "moderate"
        else:
            return "low"
