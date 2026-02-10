from ses_intelligence.behavior_graph import BehaviorGraph

_behavior_graph = None

def get_behavior_graph():
    global _behavior_graph
    if _behavior_graph is None:
        _behavior_graph = BehaviorGraph()
    return _behavior_graph
