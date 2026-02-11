from .change_model import BehaviorChange
from .diff import GraphDiff


def analyze_diff(diff: GraphDiff):
    changes = []
    explanations = []

    # --- New Edges ---
    for (src, dst) in diff.new_edges:
        changes.append(
            BehaviorChange(
                type="edge_added",
                src=src,
                dst=dst,
            )
        )
        explanations.append(
            f"New execution path detected: `{src}` now calls `{dst}`."
        )

    # --- Removed Edges ---
    for (src, dst) in diff.removed_edges:
        changes.append(
            BehaviorChange(
                type="edge_removed",
                src=src,
                dst=dst,
            )
        )
        explanations.append(
            f"Execution path removed: `{src}` no longer calls `{dst}`."
        )

    # --- Timing Changes ---
    for (src, dst), metrics in diff.changed_edges.items():
        old_avg = metrics["old_avg"]
        new_avg = metrics["new_avg"]
        delta = metrics["delta_pct"]

        if delta > 0:
            change_type = "timing_regression"
            explanations.append(
                f"`{src}` → `{dst}` became slower ({delta:.2f}% increase)."
            )
        else:
            change_type = "timing_improvement"
            explanations.append(
                f"`{src}` → `{dst}` became faster ({abs(delta):.2f}% decrease)."
            )

        changes.append(
            BehaviorChange(
                type=change_type,
                src=src,
                dst=dst,
                metric_before=old_avg,
                metric_after=new_avg,
            )
        )

    if not explanations:
        explanations.append("No significant behavior changes detected.")

    return changes, explanations
