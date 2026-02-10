import networkx as nx

class BehaviorGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_call(self, caller, callee, duration):
        if not self.graph.has_node(caller):
            self.graph.add_node(caller)

        if not self.graph.has_node(callee):
            self.graph.add_node(callee)

        if self.graph.has_edge(caller, callee):
            self.graph[caller][callee]["count"] += 1
            self.graph[caller][callee]["total_duration"] += duration
        else:
            self.graph.add_edge(
                caller,
                callee,
                count=1,
                total_duration=duration
            )

    def summary(self):
        summary = []
        for caller, callee, data in self.graph.edges(data=True):
            avg_time = data["total_duration"] / data["count"]
            summary.append({
                "caller": caller,
                "callee": callee,
                "calls": data["count"],
                "avg_duration": round(avg_time, 4)
            })
        return summary
