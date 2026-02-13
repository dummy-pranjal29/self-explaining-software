import numpy as np
from sklearn.linear_model import LogisticRegression


class RiskForecaster:
    """
    Predicts future instability probability.
    """

    def __init__(self):
        self.model = LogisticRegression()
        self.trained = False

    def train(self, feature_matrix, labels):
        """
        feature_matrix: 2D list
        labels: binary list (future instability)
        """
        if len(feature_matrix) < 5:
            return

        self.model.fit(feature_matrix, labels)
        self.trained = True

    def predict(self, feature_matrix):
        if not self.trained:
            return [0.0 for _ in feature_matrix]

        probs = self.model.predict_proba(feature_matrix)
        return [float(p[1]) for p in probs]
