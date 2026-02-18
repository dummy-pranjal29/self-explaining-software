# ses_intelligence/tracing.py

import asyncio
import time
from functools import wraps
from typing import Callable
from ses_intelligence.runtime_state import (
    get_behavior_graph,
    push_call,
    pop_call,
    get_current_caller,
)


def trace_behavior(func: Callable) -> Callable:
    """
    Decorator to trace function behavior and build architecture graph.
    
    Supports both synchronous and asynchronous functions.
    
    Args:
        func: The function to trace
        
    Returns:
        Wrapped function that traces behavior
    """
    # Check if the function is async
    is_async = asyncio.iscoroutinefunction(func)
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get parent BEFORE pushing current function
        caller = get_current_caller()
        callee = func.__name__

        graph = get_behavior_graph()

        # Push current function onto stack
        push_call(callee)

        try:
            start = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start

            # Record edge if parent exists
            if caller:
                graph.add_call(
                    caller=caller,
                    callee=callee,
                    duration=duration
                )

            print(f"[SES-FUNC] {caller} -> {callee} {duration:.4f}s")

            return result
        finally:
            pop_call()

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Get parent BEFORE pushing current function
        caller = get_current_caller()
        callee = func.__name__

        graph = get_behavior_graph()

        # Push current function onto stack
        push_call(callee)

        try:
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

            print(f"[SES-FUNC] {caller} -> {callee} {duration:.4f}s")

            return result
        finally:
            pop_call()

    # Return appropriate wrapper based on function type
    return async_wrapper if is_async else sync_wrapper


def get_edge_features():
    """Return edge features for the latest available snapshot history.

    This function is used by external API layers.
    """
    # Lazy import to avoid heavy imports at startup.
    from ses_intelligence.runtime_state import get_runtime_snapshots
    from ses_intelligence.ml.features import FeatureExtractor

    snapshots = get_runtime_snapshots()
    if not snapshots:
        return []

    extractor = FeatureExtractor(snapshots)
    feature_matrix = extractor.build_feature_matrix()
    return feature_matrix.get("edges", [])
