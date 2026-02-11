from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class BehaviorChange:
    type: Literal[
        "edge_added",
        "edge_removed",
        "timing_regression",
        "timing_improvement",
        "call_frequency_change",
    ]
    src: Optional[str] = None
    dst: Optional[str] = None
    metric_before: Optional[float] = None
    metric_after: Optional[float] = None
