# ses_intelligence/architecture_health/impact.py

import networkx as nx


class EdgeImpactAnalyzer:
    """
    Combines instability probability with
    structural importance and usage frequency.
    """

    def __init__(self, graph, edge_risk_predictions):
        self.graph = graph
        self.edge_risk_predictions = edge_risk_predictions

    def _compute_centrality(self):

        if self.graph.number_of_edges() == 0:
            return {}

        centrality = nx.betweenness_centrality(self.graph)

        max_value = max(centrality.values()) if centrality else 1

        return {
            node: (value / max_value if max_value else 0)
            for node, value in centrality.items()
        }

    def compute(self):

        if not self.edge_risk_predictions:
            return []

        centrality = self._compute_centrality()

        total_calls = sum(
            self.graph[u][v].get("call_count", 1)
            for u, v in self.graph.edges()
        ) or 1

        impact_rows = []

        for edge_info in self.edge_risk_predictions:

            edge_key = edge_info["edge"]
            caller, callee = edge_key.split("|")

            instability = edge_info["instability_probability"]

            caller_centrality = centrality.get(caller, 0)
            callee_centrality = centrality.get(callee, 0)

            structural_weight = (
                caller_centrality + callee_centrality
            ) / 2

            usage = self.graph.get_edge_data(
                caller,
                callee,
                default={}
            ).get("call_count", 1)

            usage_weight = usage / total_calls

            impact_score = (
                instability
                * (1 + structural_weight)
                * (1 + usage_weight)
            )

            impact_rows.append({
                "edge": edge_key,
                "instability_probability": instability,
                "structural_weight": round(structural_weight, 4),
                "usage_weight": round(usage_weight, 4),
                "impact_score": round(impact_score, 4),
            })

        impact_rows.sort(
            key=lambda x: x["impact_score"],
            reverse=True
        )

        return impact_rows
