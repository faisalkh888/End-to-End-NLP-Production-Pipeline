"""Compute paired judge win rate and percentile bootstrap confidence interval."""
import argparse
import json
import random
from pathlib import Path


def summarize(rows, iterations=5000, seed=7):
    # judge labels: A, B, tie. Candidate is B; ties count as half a win.
    values = [1.0 if x == "B" else 0.0 if x == "A" else 0.5 for x in rows]
    if not values:
        raise ValueError("at least one pairwise judgment is required")
    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return {"n": len(values), "candidate_win_rate_ties_half": sum(values) / len(values),
            "ci95_percentile": [means[int(.025 * iterations)], means[min(iterations-1, int(.975 * iterations))]],
            "bootstrap_iterations": iterations, "seed": seed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("judgments", type=Path)
    parser.add_argument("--iterations", type=int, default=5000)
    args = parser.parse_args()
    records = [json.loads(x) for x in args.judgments.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(json.dumps(summarize([x["winner"] for x in records], args.iterations), indent=2))
