"""ses_intelligence.runtime_state

Thread-local runtime state used by the tracing middleware/decorators.

This module also exposes small helper APIs used by Django views.
Historically, views expected a `get_runtime_snapshots()` function, but it
was never implemented, which breaks `python manage.py check`.
"""

import threading
from typing import Dict, List, Optional, Tuple

import networkx as nx

from ses_intelligence.behavior_graph import BehaviorGraph
from ses_intelligence.behavior_change.history import SnapshotStore


_thread_local = threading.local()


class RuntimeSnapshot:
    """Lightweight snapshot object compatible with the ML/health engines.

    The intelligence layer expects each snapshot to have:
      - `.graph`: a `networkx.DiGraph`
      - `.edge_signature`: dict[(caller, callee)] -> {call_count, avg_duration}
    """

    def __init__(
        self,
        *,
        graph: nx.DiGraph,
        edge_signature: Dict[Tuple[str, str], Dict],
        snapshot_id: Optional[str] = None,
    ):
        self.graph = graph
        self.edge_signature = edge_signature
        self.snapshot_id = snapshot_id


# ------------------------------------------------------------
# GRAPH ACCESS
# ------------------------------------------------------------

def get_behavior_graph():
    if not hasattr(_thread_local, "graph"):
        _thread_local.graph = BehaviorGraph()
    return _thread_local.graph


# ------------------------------------------------------------
# CALL STACK MANAGEMENT
# ------------------------------------------------------------

def push_call(func_name: str):
    if not hasattr(_thread_local, "call_stack"):
        _thread_local.call_stack = []
    _thread_local.call_stack.append(func_name)


def pop_call():
    if hasattr(_thread_local, "call_stack") and _thread_local.call_stack:
        _thread_local.call_stack.pop()


def get_current_caller():
    """
    Returns the current parent BEFORE pushing new function.
    """
    if hasattr(_thread_local, "call_stack") and _thread_local.call_stack:
        return _thread_local.call_stack[-1]
    return None


# ------------------------------------------------------------
# RESET PER REQUEST
# ------------------------------------------------------------

def reset_runtime_state():
    _thread_local.graph = BehaviorGraph()
    _thread_local.call_stack = []


# ------------------------------------------------------------
# SNAPSHOT ACCESS (used by API)
# ------------------------------------------------------------


def _reconstruct_snapshots(records: List[Dict]) -> List[RuntimeSnapshot]:
    """Reconstruct `RuntimeSnapshot` objects from on-disk snapshot records."""
    snapshots: List[RuntimeSnapshot] = []

    for record in records:
        serialized = record.get("edge_signature", {})
        edge_signature: Dict[Tuple[str, str], Dict] = {
            tuple(edge_key.split("|")): meta for edge_key, meta in serialized.items()
        }

        graph = nx.DiGraph()
        for (u, v), meta in edge_signature.items():
            call_count = int(meta.get("call_count", 0) or 0)
            avg_duration = float(meta.get("avg_duration", 0.0) or 0.0)

            # Keep both naming conventions for compatibility.
            graph.add_edge(
                u,
                v,
                call_count=call_count,
                avg_duration=avg_duration,
                count=call_count,
                total_duration=avg_duration * call_count,
            )

        snapshots.append(
            RuntimeSnapshot(
                graph=graph,
                edge_signature=edge_signature,
                snapshot_id=record.get("snapshot_id"),
            )
        )

    return snapshots


def get_runtime_snapshots(limit: Optional[int] = None) -> List[RuntimeSnapshot]:
    """Return snapshots for health/intelligence computations.

    Preference order:
      1) On-disk snapshots from `behavior_data/snapshots` (append-only)
      2) A single in-memory snapshot derived from the current thread-local graph
    """
    records = SnapshotStore.load_all()
    if records:
        snapshots = _reconstruct_snapshots(records)
        return snapshots[-limit:] if limit else snapshots

    # Fallback: construct a single snapshot from the current runtime graph.
    behavior_graph = get_behavior_graph()
    graph = behavior_graph.graph.copy()

    edge_signature: Dict[Tuple[str, str], Dict] = {}
    for u, v, data in graph.edges(data=True):
        call_count = int(data.get("count", data.get("call_count", 0)) or 0)
        total_duration = data.get("total_duration")
        if total_duration is None:
            total_duration = float(data.get("avg_duration", 0.0) or 0.0) * call_count

        avg_duration = (float(total_duration) / call_count) if call_count > 0 else 0.0
        edge_signature[(str(u), str(v))] = {
            "call_count": call_count,
            "avg_duration": avg_duration,
        }

    # Even with zero edges, having a graph can be useful (health score becomes 100).
    if graph.number_of_nodes() == 0 and graph.number_of_edges() == 0:
        return []

    return [
        RuntimeSnapshot(
            graph=graph,
            edge_signature=edge_signature,
            snapshot_id="in_memory",
        )
    ]
