"""ses_intelligence.runtime_state

Thread-safe runtime state with global project registry.

ARCHITECTURE:
- Global project registry stores graphs per project_id (NOT per thread)
- Each project graph is protected by a threading.Lock()
- Call stack remains thread-local to track current call context
- Snapshots are auto-persisted every N calls
- Multi-project isolation guaranteed

This module also exposes small helper APIs used by Django views.
"""

import threading
from typing import Dict, List, Optional, Tuple
import time
import logging

import networkx as nx

from ses_intelligence.behavior_graph import BehaviorGraph
from ses_intelligence.behavior_change.history import SnapshotStore

logger = logging.getLogger(__name__)

# Thread-local call stack (local context only, not global state)
_thread_local = threading.local()

# Global project registry: {project_id: {graph, lock, call_count}}
_project_registry: Dict[str, Dict] = {}
_registry_lock = threading.Lock()

# Configuration
SNAPSHOT_INTERVAL = 10  # Auto-persist snapshot after N calls


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
# PROJECT REGISTRY INITIALIZATION & ACCESS
# ------------------------------------------------------------

def _get_project_id() -> str:
    """Get current project_id from global configuration."""
    try:
        from ses_intelligence.config import get_config
        config = get_config()
        if config:
            return config.project_id
    except (ImportError, RuntimeError):
        pass
    return "default"


def _ensure_project_initialized(project_id: str):
    """Ensure project exists in registry. Creates if not present."""
    if project_id not in _project_registry:
        with _registry_lock:
            # Double-check pattern: another thread might have created it
            if project_id not in _project_registry:
                _project_registry[project_id] = {
                    "graph": BehaviorGraph(),
                    "lock": threading.Lock(),
                    "call_count": 0,
                }


def get_behavior_graph(project_id: Optional[str] = None) -> BehaviorGraph:
    """
    Get thread-safe behavior graph for a project.
    
    Graph is stored globally per project, NOT per thread.
    Concurrent threads all see the same graph for the same project.
    """
    project_id = project_id or _get_project_id()
    _ensure_project_initialized(project_id)
    return _project_registry[project_id]["graph"]


def _get_project_lock(project_id: Optional[str] = None) -> threading.Lock:
    """Get the lock for a project."""
    project_id = project_id or _get_project_id()
    _ensure_project_initialized(project_id)
    return _project_registry[project_id]["lock"]


def _increment_call_count(project_id: Optional[str] = None):
    """Increment call count and check if snapshot should be persisted."""
    project_id = project_id or _get_project_id()
    _ensure_project_initialized(project_id)
    
    with _registry_lock:
        _project_registry[project_id]["call_count"] += 1
        call_count = _project_registry[project_id]["call_count"]
    
    # Auto-persist snapshot
    if call_count % SNAPSHOT_INTERVAL == 0:
        _persist_snapshot(project_id)


def _persist_snapshot(project_id: Optional[str] = None):
    """Auto-persist current graph state to SnapshotStore."""
    project_id = project_id or _get_project_id()
    
    try:
        from ses_intelligence.behavior_change.snapshot import BehaviorSnapshot
        
        graph_obj = get_behavior_graph(project_id)
        lock = _get_project_lock(project_id)
        
        # Create snapshot in thread-safe manner
        with lock:
            snapshot = BehaviorSnapshot(graph_obj, label=f"auto_{project_id}_{int(time.time())}")
        
        # Persist to store
        store = SnapshotStore(project_id=project_id)
        store.save(snapshot, project_id=project_id)
        logger.debug(f"[SES] Auto-persisted snapshot for project {project_id}")
    except Exception as e:
        logger.warning(f"[SES] Failed to auto-persist snapshot: {e}")


# ------------------------------------------------------------
# GRAPH ACCESS
# DEPRECATED: Use get_behavior_graph(project_id) instead
# Kept for backward compatibility
# ------------------------------------------------------------

def _get_behavior_graph():
    """Legacy function. Use get_behavior_graph() instead."""
    return get_behavior_graph()





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

def reset_runtime_state(project_id: Optional[str] = None):
    """Reset runtime state for a project or current project."""
    project_id = project_id or _get_project_id()
    _ensure_project_initialized(project_id)
    
    with _registry_lock:
        _project_registry[project_id] = {
            "graph": BehaviorGraph(),
            "lock": threading.Lock(),
            "call_count": 0,
        }
    
    # Also reset thread-local call stack
    if hasattr(_thread_local, "call_stack"):
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


def get_runtime_snapshots(
    limit: Optional[int] = None, 
    project_id: Optional[str] = None
) -> List[RuntimeSnapshot]:
    """Return snapshots for health/intelligence computations.

    Preference order:
      1) On-disk snapshots from project-specific storage (append-only)
      2) A single in-memory snapshot derived from the current graph
    
    This function is thread-safe. Multiple threads accessing the same
    project_id will see consistent snapshots.
    
    Args:
        limit: Optional limit on number of snapshots to return
        project_id: Optional project identifier. Uses current project if not provided.
    
    Returns:
        List of RuntimeSnapshot objects. Never empty if graph has been used.
    """
    project_id = project_id or _get_project_id()
    
    # Create SnapshotStore with project_id
    store = SnapshotStore(project_id=project_id)
    records = store.load_all()
    
    if records:
        snapshots = _reconstruct_snapshots(records)
        return snapshots[-limit:] if limit else snapshots

    # Fallback: construct a single snapshot from the current runtime graph.
    # Use lock to safely read the graph
    graph_obj = get_behavior_graph(project_id)
    lock = _get_project_lock(project_id)
    
    with lock:
        graph = graph_obj.graph.copy()

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

    # Even with zero edges, return snapshot if graph has nodes
    # (Indicates that tracing happened even if edges weren't recorded)
    return [
        RuntimeSnapshot(
            graph=graph,
            edge_signature=edge_signature,
            snapshot_id="in_memory",
        )
    ]
