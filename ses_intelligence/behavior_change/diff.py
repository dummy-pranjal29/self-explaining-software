from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

Edge = Tuple[str, str]


@dataclass
class GraphDiff:
    new_edges: set[Edge]
    removed_edges: set[Edge]
    changed_edges: Dict[Edge, Dict[str, float]]


def diff_snapshots(old, new, timing_threshold_pct: float = 20.0) -> GraphDiff:
    old_sig = old.edge_signature()
    new_sig = new.edge_signature()

    old_edges = set(old_sig.keys())
    new_edges = set(new_sig.keys())

    added = new_edges - old_edges
    removed = old_edges - new_edges

    changed = {}

    for edge in old_edges & new_edges:
        old_avg = old_sig[edge]["avg_duration"]
        new_avg = new_sig[edge]["avg_duration"]

        if old_avg == 0:
            continue

        delta_pct = ((new_avg - old_avg) / old_avg) * 100

        if abs(delta_pct) >= timing_threshold_pct:
            changed[edge] = {
                "old_avg": old_avg,
                "new_avg": new_avg,
                "delta_pct": delta_pct,
            }

    return GraphDiff(
        new_edges=added,
        removed_edges=removed,
        changed_edges=changed,
    )
