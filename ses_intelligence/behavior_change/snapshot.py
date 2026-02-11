from __future__ import annotations

import time
from .history import SnapshotStore


class BehaviorSnapshot:
    """
    Immutable snapshot of BehaviorGraph state.
    """

    def __init__(self, behavior_graph, label: str | None = None):
        self.timestamp = time.time()
        self.label = label or f"snapshot_{int(self.timestamp)}"

        # Copy underlying networkx graph
        self.graph = behavior_graph.graph.copy()

    # ------------------------------------------------------------
    # EDGE SIGNATURE
    # ------------------------------------------------------------

    def edge_signature(self):
        signature = {}

        for u, v, data in self.graph.edges(data=True):
            call_count = data.get("count", 0)
            total_duration = data.get("total_duration", 0.0)

            avg_duration = (
                total_duration / call_count
                if call_count > 0 else 0.0
            )

            signature[(u, v)] = {
                "call_count": call_count,
                "avg_duration": avg_duration,
            }

        return signature

    # ------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------

    def persist(self):
        """
        Persist this snapshot to disk.
        """
        return SnapshotStore.save(self)
