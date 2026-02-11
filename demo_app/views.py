from django.http import JsonResponse
from django.views.decorators.http import require_GET
import time

from ses_intelligence.tracing import trace_behavior
from ses_intelligence.runtime_state import get_behavior_graph

from ses_intelligence.behavior_change.snapshot import BehaviorSnapshot
from ses_intelligence.behavior_change.diff import diff_snapshots
from ses_intelligence.behavior_change.analysis import analyze_diff
from ses_intelligence.behavior_change.causal import infer_causal_hints
from ses_intelligence.behavior_change.store import (
    get_previous_snapshot,
    save_snapshot,
)


# --------------------
# Traced application logic
# --------------------

@trace_behavior
def save_user():
    time.sleep(0.05)


@trace_behavior
def send_welcome_email():
    time.sleep(0.02)


@trace_behavior
def signup(request):
    save_user()
    send_welcome_email()
    return JsonResponse({"status": "user created"})


# --------------------
# Debug endpoints
# --------------------

@require_GET
def graph_debug(request):
    graph = get_behavior_graph()
    return JsonResponse({
        "behavior_graph": graph.summary()
    })


@require_GET
def behavior_diff_debug(request):
    """
    Compares previous and current behavior graphs,
    detects structural + timing changes,
    and infers deterministic causal hints.
    """

    current_graph = get_behavior_graph()
    current_snapshot = BehaviorSnapshot(
        current_graph,
        label="current"
    )

    previous_snapshot = get_previous_snapshot()

    # First invocation creates baseline
    if previous_snapshot is None:
        save_snapshot(current_snapshot)
        return JsonResponse({
            "status": "baseline_created",
            "message": "Initial behavior snapshot recorded."
        })

    # Structural diff
    diff = diff_snapshots(previous_snapshot, current_snapshot)

    # Convert diff → structured changes + explanations
    changes, explanations = analyze_diff(diff)

    # Infer causal relationships
    causal_hints = infer_causal_hints(changes)

    # Update baseline
    save_snapshot(current_snapshot)

    return JsonResponse({
        "status": "diff_computed",
        "changes": explanations,
        "causal_hints": causal_hints,
    })
