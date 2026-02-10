import time
import inspect
from ses_intelligence.runtime_state import get_behavior_graph

def trace_behavior(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        caller = inspect.stack()[1].function
        callee = func.__name__

        graph = get_behavior_graph()
        graph.add_call(
            caller=caller,
            callee=callee,
            duration=duration
        )

        print(f"[SES-FUNC] {caller} -> {callee} {duration:.4f}s")

        return result
    return wrapper
