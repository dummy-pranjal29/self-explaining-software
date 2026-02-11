from .snapshot import BehaviorSnapshot

_previous_snapshot: BehaviorSnapshot | None = None


def get_previous_snapshot() -> BehaviorSnapshot | None:
    return _previous_snapshot


def save_snapshot(snapshot: BehaviorSnapshot) -> None:
    global _previous_snapshot
    _previous_snapshot = snapshot