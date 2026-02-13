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
    """

    filename: str = "health_history.json"

    @property
    def path(self) -> Path:
        return HEALTH_DIR / self.filename

    # ------------------------------------------------------

    def load(self) -> List[Dict[str, Any]]:
        """
        Load the full health history as a list of records.
        Each record structure:
        {
            "timestamp": "...",
            "health": { ... full health_output dict ... }
        }
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
            # Never crash runtime intelligence due to history corruption
            return []

    # ------------------------------------------------------

    def append(self, health_output: Dict[str, Any]) -> None:
        """
        Append a single health result with timestamp metadata.
        """

        history = self.load()

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health_output,
        }

        history.append(record)

        # Full rewrite (safe for small files)
        self.path.write_text(
            json.dumps(history, indent=2, default=str),
            encoding="utf-8",
        )
