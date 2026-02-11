def infer_causal_hints(changes):
    hints = []

    added_edges = [
        c for c in changes if c.type == "edge_added"
    ]

    regressions = [
        c for c in changes if c.type == "timing_regression"
    ]

    improvements = [
        c for c in changes if c.type == "timing_improvement"
    ]

    # Rule 1: New edge + slowdown from same source
    for added in added_edges:
        for reg in regressions:
            if reg.src == added.src:
                hints.append(
                    f"The slowdown in `{added.src}` coincides with a new call to `{added.dst}`."
                )

    # Rule 2: Removed edge + improvement
    removed_edges = [
        c for c in changes if c.type == "edge_removed"
    ]

    for removed in removed_edges:
        for imp in improvements:
            if imp.src == removed.src:
                hints.append(
                    f"`{removed.src}` became faster after removing a call to `{removed.dst}`."
                )

    return hints
