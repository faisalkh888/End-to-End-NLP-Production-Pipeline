"""Evaluate a running triage endpoint on a frozen JSONL set and emit gate-ready metrics."""
import argparse
import json
import os
import time
from pathlib import Path

import httpx

from evals.metrics import json_validity, macro_f1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("evals/data/triage.jsonl"))
    parser.add_argument("--endpoint", default="http://localhost:8000")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--api-token", default=os.getenv("API_TOKEN", ""))
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    fields = ("category", "priority", "product_area")
    gold = {field: [] for field in fields}
    predicted = {field: [] for field in fields}
    serialized = []
    headers = {"Authorization": f"Bearer {args.api_token}"} if args.api_token else {}
    checkpoint_path = args.output.with_suffix(args.output.suffix + ".progress.jsonl") if args.output else None
    completed = {}
    if checkpoint_path and checkpoint_path.exists():
        for line in checkpoint_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                index = int(item["index"])
                if 1 <= index <= len(rows) and item.get("ticket") == rows[index - 1]["ticket"]:
                    completed[index] = item["response"]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                # Ignore a truncated final line; successful records are one per line.
                continue

    if checkpoint_path:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Resuming evaluation: {len(completed)}/{len(rows)} predictions already saved", flush=True)
    with httpx.Client(timeout=60, headers=headers) as client:
        for index, row in enumerate(rows, start=1):
            if index in completed:
                raw = completed[index]
            else:
                while True:
                    response = client.post(
                        f"{args.endpoint.rstrip('/')}/v1/triage", json={"ticket": row["ticket"]}
                    )
                    if response.status_code != 429:
                        response.raise_for_status()
                        break
                    retry_after = max(1, int(response.headers.get("Retry-After", "5")))
                    print(f"Rate limited; retrying ticket {index}/{len(rows)} in {retry_after}s", flush=True)
                    time.sleep(retry_after)
                raw = response.text
                if checkpoint_path:
                    with checkpoint_path.open("a", encoding="utf-8") as checkpoint:
                        checkpoint.write(json.dumps({"index": index, "ticket": row["ticket"], "response": raw}) + "\n")
                        checkpoint.flush()
            serialized.append(raw)
            value = response.json()
            for field in fields:
                gold[field].append(str(row["label"][field]))
                predicted[field].append(str(value.get(field, "")))
            if index % 5 == 0 or index == len(rows):
                print(f"Evaluated {index}/{len(rows)} tickets", flush=True)

    result = {
        "examples": len(rows),
        "triage_json_validity": json_validity(serialized),
        "triage_macro_f1": macro_f1(gold["category"], predicted["category"]),
        **{
            f"{field}_accuracy": sum(a == b for a, b in zip(gold[field], predicted[field]))
            / max(1, len(gold[field]))
            for field in fields
        },
        "data_status": "Use only as evidence for the supplied manually reviewed evaluation set.",
    }
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
