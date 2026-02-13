import numpy as np


class EscalationDetector:
    """
    Detects anomaly streak escalation.
    """

    def __init__(self, anomaly_scores_by_snapshot):
        """
        anomaly_scores_by_snapshot:
        {
            edge: [score_t1, score_t2, ...]
        }
        """
        self.data = anomaly_scores_by_snapshot

    def compute(self):
        results = {}

        for edge, scores in self.data.items():
            if not scores:
                continue

            consecutive = 0
            max_streak = 0

            for score in scores[::-1]:
                if score > 0:
                    consecutive += 1
                else:
                    break

            max_streak = consecutive

            if len(scores) >= 2:
                slope = np.polyfit(range(len(scores)), scores, 1)[0]
            else:
                slope = 0.0

            density = sum(1 for s in scores[-5:] if s > 0) / min(5, len(scores))

            escalation_index = (
                0.4 * (max_streak / max(1, len(scores))) +
                0.3 * max(0, slope) +
                0.3 * density
            )

            escalation_index = float(max(0.0, min(1.0, escalation_index)))

            results[edge] = escalation_index

        return results
