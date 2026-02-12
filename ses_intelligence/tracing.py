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
