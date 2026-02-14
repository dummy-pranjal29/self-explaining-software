# ses_intelligence/tracing.py

import time
from functools import wraps
from ses_intelligence.runtime_state import (
    get_behavior_graph,
    push_call,
    pop_call,
    get_current_caller,
)


def trace_behavior(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        # Get parent BEFORE pushing current function
        caller = get_current_caller()
        callee = func.__name__

        graph = get_behavior_graph()

        # Push current function onto stack
        push_call(callee)

        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        # Record edge if parent exists
        if caller:
            graph.add_call(
                caller=caller,
                callee=callee,
                duration=duration
            )

        pop_call()

        print(f"[SES-FUNC] {caller} -> {callee} {duration:.4f}s")

        return result

    return wrapper


def get_edge_features():
    """Return edge features for the latest available snapshot history.

    This function is used by the Django API layer.
    """
    # Lazy import to avoid heavy imports at Django startup.
    from ses_intelligence.runtime_state import get_runtime_snapshots
    from ses_intelligence.ml.features import FeatureExtractor

    snapshots = get_runtime_snapshots()
    if not snapshots:
        return []

    extractor = FeatureExtractor(snapshots)
    feature_matrix = extractor.build_feature_matrix()
    return feature_matrix.get("edges", [])
