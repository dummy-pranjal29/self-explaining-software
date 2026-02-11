from .diff import GraphDiff

def explain_diff(diff: GraphDiff) -> list[str]:
    explanations = []

    for caller, callee in diff.new_edges:
        explanations.append(
            f"New execution path detected: `{caller}` now calls `{callee}`."
        )

    for caller, callee in diff.removed_edges:
        explanations.append(
            f"Execution path removed: `{caller}` no longer calls `{callee}`."
        )

    for (caller, callee), change in diff.changed_edges.items():
        direction = "slower" if change["delta_pct"] > 0 else "faster"
        explanations.append(
            f"`{caller} → {callee}` became {direction}: "
            f"{change['old_avg']:.2f}ms → {change['new_avg']:.2f}ms "
            f"({change['delta_pct']:.1f}%)."
        )

    if not explanations:
        explanations.append("No significant behavior changes detected.")

    return explanations
