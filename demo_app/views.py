from django.http import JsonResponse

from ses_intelligence.behavior_graph import get_behavior_graph
from ses_intelligence.behavior_change.snapshot import BehaviorSnapshot
from ses_intelligence.behavior_change.diff import diff_snapshots
from ses_intelligence.behavior_change.analysis import analyze_diff
from ses_intelligence.behavior_change.causal import infer_causal_hints

from ses_intelligence.behavior_change.history import (
    SnapshotStore,
    build_edge_lifecycle,
    build_timing_history,
    detect_monotonic_increase,
    detect_edge_disappearance,
)


# ------------------------------------------------------------
# EXISTING APP ENDPOINTS
# ------------------------------------------------------------

def signup(request):
    return JsonResponse({"status": "signup endpoint"})


def graph_debug(request):
    graph = get_behavior_graph()
    return JsonResponse({
        "summary": graph.summary()
    })


# ------------------------------------------------------------
# DIFF ENDPOINT
# ------------------------------------------------------------

def behavior_diff_debug(request):
    graph = get_behavior_graph()
    new_snapshot = BehaviorSnapshot(graph)

    snapshots = SnapshotStore.load_all()

    if not snapshots:
        new_snapshot.persist()
        return JsonResponse({"status": "initial_snapshot_created"})

    last_snapshot_record = snapshots[-1]

    old_signature = {
        tuple(edge.split("|")): meta
        for edge, meta in last_snapshot_record["edge_signature"].items()
    }

    class StoredSnapshot:
        def edge_signature(self):
            return old_signature

    previous_snapshot = StoredSnapshot()

    graph_diff = diff_snapshots(previous_snapshot, new_snapshot)

    changes, explanations = analyze_diff(graph_diff)
    causal_hints = infer_causal_hints(changes)

    new_snapshot.persist()

    return JsonResponse({
        "status": "diff_computed",
        "changes": [c.to_dict() for c in changes],
        "explanations": explanations,
        "causal_hints": causal_hints,
    })



# ------------------------------------------------------------
# HISTORY ENDPOINT
# ------------------------------------------------------------

def behavior_history_debug(request):
    snapshots = SnapshotStore.load_all()

    if not snapshots:
        return JsonResponse({
            "status": "no_snapshots",
            "total_snapshots": 0
        })

    lifecycle = build_edge_lifecycle(snapshots)
    timing_history = build_timing_history(snapshots)

    latest_snapshot_id = snapshots[-1]["snapshot_id"]

    drifting_edges = detect_monotonic_increase(timing_history)
    disappeared_edges = detect_edge_disappearance(
        lifecycle,
        latest_snapshot_id
    )

    return JsonResponse({
        "status": "history_computed",
        "total_snapshots": len(snapshots),
        "tracked_edges": len(lifecycle),
        "drifting_edges": drifting_edges,
        "disappeared_edges": disappeared_edges,
    })
