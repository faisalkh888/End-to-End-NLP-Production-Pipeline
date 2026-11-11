"""Small local retrieval evaluation; full answer judging requires a reviewed judge configuration."""
import argparse
import json
from pathlib import Path
from serving.retrieval import make_retriever
from evals.metrics import recall_at_k


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("evals/data/qa.jsonl"))
    args = parser.parse_args()
    retriever = make_retriever()
    retriever.index_directory(Path("data/docs"))
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    scores = [recall_at_k(set(x["relevant_document_ids"]),
                          [p["document_id"] for p in retriever.search(x["question"], x.get("access_level", "public"))]) for x in rows]
    result = {"examples": len(scores), "recall_at_5": sum(scores) / max(1, len(scores))}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
