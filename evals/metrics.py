from collections import Counter
from math import sqrt


def recall_at_k(relevant: set[str], retrieved: list[str], k: int = 5) -> float:
    return len(relevant.intersection(retrieved[:k])) / max(1, len(relevant))


def macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    labels = set(y_true) | set(y_pred)
    scores = []
    for label in labels:
        tp = sum(a == label and b == label for a, b in zip(y_true, y_pred))
        fp = sum(a != label and b == label for a, b in zip(y_true, y_pred))
        fn = sum(a == label and b != label for a, b in zip(y_true, y_pred))
        p, r = tp / max(1, tp + fp), tp / max(1, tp + fn)
        scores.append(2 * p * r / max(1e-12, p + r))
    return sum(scores) / max(1, len(scores))


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if not total:
        return 0.0, 0.0
    p = successes / total
    d = 1 + z*z/total
    center = (p + z*z/(2*total)) / d
    margin = z * sqrt((p*(1-p) + z*z/(4*total))/total) / d
    return max(0, center-margin), min(1, center+margin)


def json_validity(outputs: list[str]) -> float:
    import json
    valid = 0
    for value in outputs:
        try:
            obj = json.loads(value)
            valid += int({"category", "priority", "product_area", "summary"} <= set(obj))
        except (ValueError, TypeError):
            pass
    return valid / max(1, len(outputs))
