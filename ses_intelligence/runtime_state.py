# ses_intelligence/runtime_state.py

import threading
from ses_intelligence.behavior_graph import BehaviorGraph


_thread_local = threading.local()


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
