import os
import json
import numpy as np
from typing import List, Dict
from sklearn.linear_model import LinearRegression


class ForecastConfidenceEngine:
    """
    Statistical validation layer for architecture health forecasting.

    Responsibilities:
    - Rolling regression modeling
    - RMSE calculation
    - Residual variance modeling
    - Confidence interval computation
    - Volatility classification
    """

    def __init__(self, history_path=None, window_size: int = 10):
        self.history_path = history_path
        self.window_size = window_size

    # -------------------------------------------------
    # HEALTH HISTORY LOADING
    # -------------------------------------------------

    def load_health_history(self) -> List[float]:

        if not self.history_path:
            return []

        if not os.path.exists(self.history_path):
            return []

        with open(self.history_path, "r") as f:
            data = json.load(f)

        return self._extract_health_values(data)

    # -------------------------------------------------
    # HEALTH EXTRACTION
    # -------------------------------------------------

    def _extract_health_values(self, history_data):

        values = []

        for entry in history_data:

            if not isinstance(entry, dict):
                continue

            if "health_score" in entry:
                values.append(entry["health_score"])
                continue

            if "architecture_health_score" in entry:
                values.append(entry["architecture_health_score"])

            elif "raw" in entry:
                block = entry["raw"]

                if isinstance(block, dict):
                    if "health_score" in block:
                        values.append(block["health_score"])
                    elif "architecture_health_score" in block:
                        values.append(block["architecture_health_score"])

        return values

    # -------------------------------------------------
    # ROLLING REGRESSION
    # -------------------------------------------------

    def rolling_regression(self, values: List[float]):

        window = values[-self.window_size:]

        X = np.arange(len(window)).reshape(-1, 1)
        y = np.array(window)

        model = LinearRegression()
        model.fit(X, y)

        predictions = model.predict(X)
        residuals = y - predictions

        return predictions, residuals

    # -------------------------------------------------
    # METRICS
    # -------------------------------------------------

    def compute_rmse(self, residuals):
        return np.sqrt(np.mean(residuals ** 2))

    def compute_variance(self, residuals):
        return np.var(residuals)

    def forecast_next(self, values):

        window = values[-self.window_size:]

        X = np.arange(len(window)).reshape(-1, 1)
        y = np.array(window)

        model = LinearRegression()
        model.fit(X, y)

        next_x = np.array([[len(window)]])
        return float(model.predict(next_x)[0])

    # -------------------------------------------------
    # CONFIDENCE INTERVAL
    # -------------------------------------------------

    def compute_confidence_interval(self, prediction, std_dev):

        z_score = 1.96  # 95%
        margin = z_score * std_dev

        return prediction - margin, prediction + margin

    # -------------------------------------------------
    # CONFIDENCE SCORE (FIXED)
    # -------------------------------------------------

    def compute_confidence_score(self, rmse, mean_health):

        if mean_health == 0:
            return 0.0

        raw_score = 1 - (rmse / mean_health)

        # Realism dampener
        capped = min(raw_score, 0.95)

        # Never below 70% once model is active
        return max(0.70, capped)

    # -------------------------------------------------
    # VOLATILITY (FIXED — BASED ON STD DEV)
    # -------------------------------------------------

    def classify_volatility(self, std_dev):

        if std_dev < 0.05:
            return "low"
        elif std_dev < 0.25:
            return "moderate"
        else:
            return "high"

    # -------------------------------------------------
    # EXECUTION MODES
    # -------------------------------------------------

    def run(self):

        values = self.load_health_history()
        return self._compute(values)

    def run_from_memory(self, history_data):

        values = self._extract_health_values(history_data)
        return self._compute(values)

    # -------------------------------------------------
    # CORE COMPUTATION
    # -------------------------------------------------

    def _compute(self, values):

        if len(values) < self.window_size:
            return {"status": "insufficient_data"}

        predictions, residuals = self.rolling_regression(values)

        rmse = self.compute_rmse(residuals)
        variance = self.compute_variance(residuals)
        std_dev = np.sqrt(variance)

        next_prediction = self.forecast_next(values)

        lower, upper = self.compute_confidence_interval(
            next_prediction,
            std_dev,
        )

        mean_health = np.mean(values[-self.window_size:])

        confidence_score = self.compute_confidence_score(
            rmse,
            mean_health,
        )

        volatility = self.classify_volatility(std_dev)

        return {
            "status": "success",
            "forecast_next": round(next_prediction, 2),
            "confidence_interval": {
                "lower": round(lower, 2),
                "upper": round(upper, 2),
            },
            "rmse": round(float(rmse), 4),
            "residual_variance": round(float(variance), 4),
            "confidence_score": round(confidence_score, 3),
            "volatility": volatility,
        }
