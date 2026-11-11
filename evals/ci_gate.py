"""Promotion gate: compare candidate metrics with frozen champion and absolute floors."""
import json
import sys
from pathlib import Path

candidate, champion = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])
floors = {"recall_at_5": 0.80, "faithfulness": 0.85, "triage_json_validity": 0.99}
for metric, floor in floors.items():
    if candidate.get(metric, 0) < floor:
        raise SystemExit(f"BLOCK: {metric}={candidate.get(metric)} below required floor {floor}")
    if candidate[metric] + 1e-9 < champion.get(metric, 0):
        raise SystemExit(f"BLOCK: {metric} regressed from champion {champion[metric]} to {candidate[metric]}")
print("PASS: candidate meets configured floors and does not regress against champion")
