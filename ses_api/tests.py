import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase


class ForecastApiTests(TestCase):
    def test_forecast_recomputed_from_history_when_persisted_output_missing(self):
        with TemporaryDirectory() as tmp:
            base_path = Path(tmp)

            history = []
            for i in range(12):
                score = 80 + i
                history.append(
                    {
                        "timestamp": f"2026-01-01T00:00:{i:02d}Z",
                        "health_score": float(score),
                        "raw": {
                            "health_score": float(score),
                            "edge_count": 10,
                            "edges": [],
                        },
                    }
                )

            (base_path / "health_history.json").write_text(
                json.dumps(history),
                encoding="utf-8",
            )

            with patch("ses_api.views.BASE_PATH", str(base_path)):
                response = self.client.get("/api/forecast/")

            self.assertEqual(response.status_code, 200)

            payload = response.json()
            self.assertIn("forecast", payload)
            self.assertIsInstance(payload["forecast"], dict)
            self.assertEqual(payload["forecast"].get("status"), "success")
            self.assertIn("forecast_next", payload["forecast"])

    def test_forecast_prefers_non_empty_persisted_output(self):
        with TemporaryDirectory() as tmp:
            base_path = Path(tmp)

            expected = {
                "status": "success",
                "forecast_next": 91.2,
                "confidence_interval": {"lower": 88.1, "upper": 94.3},
            }

            (base_path / "forecast_output.json").write_text(
                json.dumps(expected),
                encoding="utf-8",
            )

            with patch("ses_api.views.BASE_PATH", str(base_path)):
                response = self.client.get("/api/forecast/")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get("forecast"), expected)
