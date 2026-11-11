"""Evaluate QA answer text and citations against a small reviewed JSONL set."""
import argparse
import json
import os
import re
import time
from pathlib import Path

import httpx


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("evals/data/qa_answer_eval.jsonl"))
    parser.add_argument("--endpoint", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("evals/results/qa_answer_eval.json"))
    parser.add_argument(
        "--in-process", action="store_true",
        help="evaluate the local FastAPI app with an isolated evaluation token instead of HTTP",
    )
    parser.add_argument(
        "--caller-access-level", choices=("public", "support", "engineering"),
        default="engineering",
        help="clearance for --in-process evaluation (defaults to engineering)",
    )
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.in_process:
        # Keep local evaluation auth isolated from the running Compose API.
        token = "atlas-local-eval-only"
        os.environ["API_TOKEN"] = token
        os.environ["API_CALLER_ACCESS_LEVEL"] = args.caller_access_level
        from fastapi.testclient import TestClient
        from serving.app import app

        client_context = TestClient(app)
        request_url = "/v1/qa"
        evaluation_mode = f"in-process, caller clearance={args.caller_access_level}"
    else:
        token = os.getenv("ATLAS_API_TOKEN", "")
        client_context = httpx.Client(timeout=90)
        request_url = f"{args.endpoint.rstrip('/')}/v1/qa"
        evaluation_mode = f"http endpoint={args.endpoint.rstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    results = []
    with client_context as client:
        for index, row in enumerate(rows, start=1):
            payload = {"question": row["question"], "access_level": row["access_level"]}
            response = None
            for attempt in range(4):
                response = client.post(request_url, json=payload, headers=headers)
                if response.status_code != 429 or attempt == 3:
                    break
                delay = int(response.headers.get("Retry-After", "2"))
                time.sleep(max(1, delay))

            item = {
                "question": row["question"],
                "expected_document_id": row["expected_document_id"],
                "acceptable_document_ids": row.get("acceptable_document_ids", [row["expected_document_id"]]),
                "http_status": response.status_code,
            }
            if response.is_success:
                body = response.json()
                citations = [citation.get("document_id") for citation in body.get("citations", [])]
                answer = body.get("answer", "")
                accepted_ids = set(item["acceptable_document_ids"])
                item.update({
                    "answer": answer,
                    "refused": bool(body.get("refused", False)),
                    "citations": citations,
                    "answer_match": normalize(row["expected_answer"]) in normalize(answer),
                    "exact_document_id_match": row["expected_document_id"] in citations,
                    "citation_match": bool(accepted_ids.intersection(citations)),
                })
            else:
                item.update({"error": response.text[:500], "answer_match": False,
                             "exact_document_id_match": False, "citation_match": False})
            results.append(item)
            print(f"Evaluated {index}/{len(rows)}")

    count = max(1, len(results))
    summary = {
        "examples": len(results),
        "evaluation_mode": evaluation_mode,
        "answer_exact_support_rate": sum(bool(x.get("answer_match")) for x in results) / count,
        "expected_citation_rate": sum(bool(x.get("citation_match")) for x in results) / count,
        "exact_document_id_rate": sum(bool(x.get("exact_document_id_match")) for x in results) / count,
        "joint_answer_and_citation_rate": sum(bool(x.get("answer_match")) and bool(x.get("citation_match")) for x in results) / count,
        "refusal_count": sum(bool(x.get("refused")) for x in results),
        "http_error_count": sum(x.get("http_status", 0) >= 400 for x in results),
        "metric_note": "Exact normalized reference-answer match; citation may match an explicitly allowed equivalent source page. Exact document-ID rate is reported separately. Synthetic corpus, not human acceptance evidence.",
        "per_example": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    printable = {key: value for key, value in summary.items() if key != "per_example"}
    print(json.dumps(printable, indent=2))
    print(f"Detailed report: {args.output}")


if __name__ == "__main__":
    main()
