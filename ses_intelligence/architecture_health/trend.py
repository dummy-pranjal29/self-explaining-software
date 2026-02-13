"""ses_intelligence.architecture_health.trend

The ML pipeline expects `ArchitectureHealthTrend` to compute a basic trend from
the stored architecture health history.

This file was previously empty, which would cause a follow-up ImportError after
fixing history.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ArchitectureHealthTrend:
    """Compute simple trend metrics over health history.

    Expected input format (from ArchitectureHealthHistory.load()):
    [
      {"timestamp": "...", "health": {"architecture_health_score": 92.0, ...}},
      ...
    ]
    """

    history: List[Dict[str, Any]]

    def _extract_scores(self) -> List[float]:
        scores: List[float] = []
        for rec in self.history or []:
            health = rec.get("health") or {}
            score = health.get("architecture_health_score")
            if isinstance(score, (int, float)):
                scores.append(float(score))
        return scores

    def compute(self) -> Dict[str, Any]:
        scores = self._extract_scores()

        if len(scores) < 2:
            return {
                "status": "insufficient_history",
                "points": len(scores),
            }

        first = scores[0]
        last = scores[-1]
        delta = last - first

        # Average change per step (very lightweight linear trend proxy)
        slope = delta / max(1, (len(scores) - 1))

        direction: Optional[str]
        if slope > 0.25:
            direction = "improving"
        elif slope < -0.25:
            direction = "degrading"
        else:
            direction = "stable"

        return {
            "status": "ok",
            "points": len(scores),
            "first_score": round(first, 2),
            "last_score": round(last, 2),
            "delta": round(delta, 2),
            "slope_per_snapshot": round(slope, 4),
            "direction": direction,
        }
