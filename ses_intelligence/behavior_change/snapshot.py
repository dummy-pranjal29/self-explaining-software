from __future__ import annotations
import time


class BehaviorSnapshot:
    def __init__(self, behavior_graph, label: str | None = None):
        """
        behavior_graph: BehaviorGraph (your wrapper, not nx.DiGraph)
        """
        self.timestamp = time.time()
        self.label = label or f"snapshot_{int(self.timestamp)}"

        # IMPORTANT: snapshot the underlying nx graph, not the wrapper
        self.graph = behavior_graph.graph.copy()

    def edge_signature(self):
        signature = {}

        for u, v, data in self.graph.edges(data=True):
            signature[(u, v)] = {
                "call_count": data.get("call_count", 0),
                "avg_duration": data.get("avg_duration", 0.0),
            }

        return signature
