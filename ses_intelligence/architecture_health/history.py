"""
ses_intelligence.architecture_health.history

Append-only persistence for architecture health results.
Used by:
- ArchitectureHealthEngine
- ArchitectureHealthTrend
- ArchitectureHealthForecaster
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


# ----------------------------------------------------------
# Directory Setup
# ----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
HEALTH_DIR = BASE_DIR / "behavior_data" / "architecture_health"
HEALTH_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------
# Architecture Health History Store
# ----------------------------------------------------------

@dataclass
class ArchitectureHealthHistory:
    """
    Append-only store for architecture health computation results.

    Each record format:
    {
        "timestamp": "...",
        "health_score": float,
        "raw": { full_health_output_dict }
    }
    """

    filename: str = "health_history.json"

    @property
    def path(self) -> Path:
        return HEALTH_DIR / self.filename

    # ------------------------------------------------------

    def load(self) -> List[Dict[str, Any]]:
        """
        Load full health history.
        Always returns a list.
        """

        if not self.path.exists():
            return []

        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return []

            data = json.loads(raw)

            if isinstance(data, list):
                return data

            return []

        except (OSError, json.JSONDecodeError):
            return []

    # ------------------------------------------------------

    def append(self, health_output: Dict[str, Any]) -> None:
        """
        Append new health record.

        health_output MUST contain:
        {
            "health_score": float,
            ...
        }
        """

        if not isinstance(health_output, dict):
            raise ValueError("health_output must be a dictionary")

        health_score = health_output.get("health_score")

        if health_score is None:
            raise ValueError("health_output missing 'health_score' key")

        history = self.load()

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": float(health_score),
            "raw": health_output,
        }

        history.append(record)

        self.path.write_text(
            json.dumps(history, indent=2, default=str),
            encoding="utf-8",
        )

    # ------------------------------------------------------

    def get_health_scores(self) -> List[float]:
        """
        Extract health score time series for forecasting.
        """

        history = self.load()

        scores: List[float] = []

        for entry in history:
            score = entry.get("health_score")
            if isinstance(score, (int, float)):
                scores.append(float(score))

        return scores
