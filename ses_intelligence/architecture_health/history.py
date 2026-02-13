"""ses_intelligence.architecture_health.history

This module was previously an empty placeholder which caused Django to fail
startup with:

    ImportError: cannot import name 'ArchitectureHealthHistory'

The runtime ML pipeline expects a small persistence helper for health outputs.
We keep it intentionally simple: append-only JSON records stored under the
project's `behavior_data/architecture_health/` directory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]
HEALTH_DIR = BASE_DIR / "behavior_data" / "architecture_health"
HEALTH_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ArchitectureHealthHistory:
    """Append-only store for architecture health computation results."""

    filename: str = "health_history.json"

    @property
    def path(self) -> Path:
        return HEALTH_DIR / self.filename

    def load(self) -> List[Dict[str, Any]]:
        """Load the full health history as a list of records."""
        if not self.path.exists():
            return []

        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            # If the file is corrupt/partial we don't want to crash Django.
            return []

    def append(self, health_output: Dict[str, Any]) -> None:
        """Append a single health result with timestamp metadata."""
        history = self.load()

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health_output,
        }

        history.append(record)

        # Atomic-ish write: write full JSON back (history files are small).
        self.path.write_text(
            json.dumps(history, indent=2, default=str),
            encoding="utf-8",
        )
