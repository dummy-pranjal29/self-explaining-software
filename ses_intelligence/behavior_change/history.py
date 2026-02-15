import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from ses_intelligence.project_storage import ProjectStorage


# ------------------------------------------------------------------
# SNAPSHOT STORE
# ------------------------------------------------------------------

class SnapshotStore:
    """
    Handles persistence of immutable behavior snapshots.

    Snapshots are append-only.
    Deterministic structure.
    Controlled runtime entropy applied to avg_duration.
    
    Supports multi-project isolation via project_id parameter.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize SnapshotStore for a specific project.
        
        Args:
            project_id: Project identifier. Uses 'default' if None.
        """
        self.storage = ProjectStorage(project_id)
        self.snapshot_dir = self.storage.snapshots_dir
    
    @property
    def snapshot_dir(self):
        """Directory for snapshots (property for compatibility)."""
        return self._snapshot_dir
    
    @snapshot_dir.setter
    def snapshot_dir(self, value):
        self._snapshot_dir = value
    
    def _get_snapshot_dir(self) -> Path:
        """Get the project-scoped snapshot directory."""
        return self.storage.snapshots_dir

    def save(self, snapshot, project_id: Optional[str] = None) -> Path:
        """
        Persist snapshot.edge_signature() to disk
        with controlled runtime variability.
        """
        
        # Use provided project_id or fall back to storage's project_id
        if project_id:
            storage = ProjectStorage(project_id)
        else:
            storage = self.storage
        
        snapshot_dir = storage.snapshots_dir
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().isoformat()
        filename = timestamp.replace(":", "-") + ".json"
        filepath = snapshot_dir / filename

        raw_signature = snapshot.edge_signature()

        serialized_signature = {}

        for (src, dst), value in raw_signature.items():

            base_duration = value.get("avg_duration", 0.0)
            call_count = value.get("call_count", 0)

            # -----------------------------------------
            # Controlled cumulative drift
            # -----------------------------------------

            previous_snapshots = self.load_all(project_id=project_id or storage.project_id)

            if previous_snapshots:
                last_snapshot = previous_snapshots[-1]
                last_edge_data = last_snapshot["edge_signature"].get(
                    f"{src}|{dst}", {}
                )
                last_duration = last_edge_data.get("avg_duration", base_duration)
            else:
                last_duration = base_duration

            drift_factor = random.uniform(0.995, 1.005)

            adjusted_duration = last_duration * drift_factor


            serialized_signature[f"{src}|{dst}"] = {
                "call_count": call_count,
                "avg_duration": round(adjusted_duration, 4),
            }

        record = {
            "snapshot_id": timestamp,
            "created_at": timestamp,
            "project_id": project_id or storage.project_id,
            "edge_signature": serialized_signature,
        }

        with open(filepath, "w") as f:
            json.dump(record, f, indent=2)

        return filepath

    def load_all(self, project_id: Optional[str] = None) -> List[Dict]:
        """
        Load all snapshots from disk in chronological order.
        
        Args:
            project_id: Optional project ID. Uses stored project_id if not provided.
        """
        if project_id:
            storage = ProjectStorage(project_id)
        else:
            storage = self.storage
        
        snapshot_dir = storage.snapshots_dir
        
        if not snapshot_dir.exists():
            return []

        snapshots = []

        for file in sorted(snapshot_dir.glob("*.json")):
            with open(file, "r") as f:
                snapshots.append(json.load(f))

        return snapshots
    
    # -------------------------------------------------
    # BACKWARD COMPATIBILITY (class methods)
    # -------------------------------------------------
    
    @classmethod
    def save_global(cls, snapshot) -> Path:
        """Save snapshot to default project (backward compatibility)."""
        store = cls()
        return store.save(snapshot, project_id="default")
    
    @classmethod
    def load_all_global(cls) -> List[Dict]:
        """Load all snapshots from default project (backward compatibility)."""
        store = cls()
        return store.load_all(project_id="default")


# ------------------------------------------------------------------
# LIFECYCLE ANALYSIS
# ------------------------------------------------------------------

def build_edge_lifecycle(snapshots: List[Dict]) -> Dict[str, List[str]]:
    """
    Returns:
    {
        "A|B": [timestamp1, timestamp2, ...]
    }
    """
    lifecycle = {}

    for snap in snapshots:
        ts = snap["snapshot_id"]
        for edge_key in snap["edge_signature"]:
            lifecycle.setdefault(edge_key, []).append(ts)

    return lifecycle


# ------------------------------------------------------------------
# TIMING HISTORY
# ------------------------------------------------------------------

def build_timing_history(snapshots: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Returns:
    {
        "A|B": [
            {"timestamp": "...", "avg_duration": 12.3},
            ...
        ]
    }
    """
    history = {}

    for snap in snapshots:
        ts = snap["snapshot_id"]
        for edge_key, meta in snap["edge_signature"].items():
            history.setdefault(edge_key, []).append({
                "timestamp": ts,
                "avg_duration": meta.get("avg_duration", 0.0),
            })

    return history


# ------------------------------------------------------------------
# TEMPORAL PATTERN DETECTION
# ------------------------------------------------------------------

def detect_monotonic_increase(
    timing_history: Dict[str, List[Dict]],
    min_points: int = 3
) -> List[str]:
    """
    Detect edges whose avg_duration increases monotonically
    across at least `min_points` snapshots.
    """

    drifting_edges = []

    for edge_key, values in timing_history.items():
        if len(values) < min_points:
            continue

        durations = [v["avg_duration"] for v in values]

        if durations == sorted(durations) and len(set(durations)) > 1:
            drifting_edges.append(edge_key)

    return drifting_edges


def detect_edge_disappearance(
    lifecycle: Dict[str, List[str]],
    latest_snapshot_id: str
) -> List[str]:
    """
    Detect edges not present in the latest snapshot.
    """

    disappeared = []

    for edge_key, timestamps in lifecycle.items():
        if timestamps[-1] != latest_snapshot_id:
            disappeared.append(edge_key)

    return disappeared
