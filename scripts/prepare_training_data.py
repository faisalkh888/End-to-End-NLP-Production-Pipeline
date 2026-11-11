"""Normalize reviewed ticket records and scrub common direct identifiers before training."""
import json
import re
from pathlib import Path

src, dst = Path("data/raw/tickets.jsonl"), Path("data/processed/triage_sft.jsonl")
dst.parent.mkdir(parents=True, exist_ok=True)
if not src.exists():
    raise SystemExit("Provide reviewed, licensed data at data/raw/tickets.jsonl; synthetic labels are not fabricated")
def scrub(text):
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b(?:\+?\d[\d .()-]{7,}\d)\b", "[PHONE]", text)
    text = re.sub(r"\b(?:sk|api|tok)_[A-Za-z0-9_-]{12,}\b", "[SECRET]", text)
    return text
with src.open(encoding="utf-8") as inp, dst.open("w", encoding="utf-8") as out:
    for line in inp:
        row = json.loads(line)
        out.write(json.dumps({"text": f"Ticket: {scrub(row['ticket'])}\nAnswer: {json.dumps(row['label'])}"}) + "\n")
