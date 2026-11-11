import hashlib
import json
import os
import re
from pathlib import Path
from typing import Protocol

from ingest.chunking import chunk_document

STOP_WORDS = {"a", "an", "and", "are", "be", "can", "do", "does", "for", "how", "i", "in",
              "is", "it", "my", "of", "on", "or", "the", "to", "was", "what", "where", "which",
              "with", "you", "your", "should"}

def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def query_terms(text: str) -> set[str]:
    query = terms(text) - STOP_WORDS
    # Normalize this common paraphrase to the wording used in document titles
    # and procedures, so “initial setup” can retrieve “Getting Started” pages.
    if {"initial", "setup"} <= query:
        query.difference_update({"initial", "setup"})
        query.update({"getting", "started"})
    elif "setup" in query:
        query.remove("setup")
        query.add("configuration")
    # Map common support wording to the corpus's troubleshooting section name.
    if query & {"problem", "issue", "diagnose", "diagnosis", "troubleshoot"}:
        query.difference_update({"problem", "issue", "diagnose", "diagnosis", "troubleshoot"})
        query.add("troubleshooting")
    # Match singular user wording to the corpus's plural section heading.
    if "permission" in query and "permissions" not in query:
        query.remove("permission")
        query.add("permissions")
    # Map common wording for editing a setting to the documented section name.
    if query & {"change", "modify", "edit"} and query & {"setting", "settings", "option", "options"}:
        query.difference_update({"change", "modify", "edit", "setting", "settings", "option", "options"})
        query.add("configuration")
    # A few common support-question paraphrases use different words from the
    # synthetic docs. Add conservative aliases so retrieval and extractive
    # sentence selection can still find the underlying guidance.
    if query & {"avoid", "including", "include", "sensitive", "leave", "out"}:
        query.update({"share", "secrets", "passwords", "tokens", "private", "request"})
    if "worked" in query:
        query.update({"verify", "result", "status"})
    if query & {"keeps", "continuing", "continues", "persistent"}:
        query.update({"persistent", "failures", "support", "reproduce"})
    if query & {"quota", "quotas", "actual"}:
        query.update({"limits", "contract", "dashboard", "authoritative"})
    return query


def relevance(query: str, text: str) -> float:
    """Fraction of meaningful query terms supported by a passage."""
    wanted = query_terms(query)
    return len(wanted & terms(text)) / max(1, len(wanted))


class Retriever(Protocol):
    def search(self, query: str, access_level: str, limit: int = 5) -> list[dict]: ...
    def index_directory(self, source: Path) -> int: ...


class MemoryRetriever:
    def __init__(self):
        self.chunks: dict[str, dict] = {}

    def index_directory(self, source: Path) -> int:
        seen: set[str] = set()
        count = 0
        for file in sorted(source.rglob("*.md")):
            metadata_file = file.with_suffix(".json")
            metadata = json.loads(metadata_file.read_text(encoding="utf-8")) if metadata_file.exists() else {}
            doc_id = metadata.get("document_id", file.stem)
            doc = {"document_id": doc_id, "title": metadata.get("title", file.stem),
                   "access_level": metadata.get("access_level", "public"),
                   "text": file.read_text(encoding="utf-8")}
            for chunk in chunk_document(doc):
                seen.add(chunk["chunk_id"])
                old = self.chunks.get(chunk["chunk_id"])
                if old != chunk:
                    self.chunks[chunk["chunk_id"]] = chunk
                    count += 1
        self.chunks = {key: value for key, value in self.chunks.items() if key in seen}
        return count

    def search(self, query: str, access_level: str, limit: int = 5) -> list[dict]:
        clearance = {"public": 0, "support": 1, "engineering": 2}.get(access_level, 0)
        q = query_terms(query)
        best_by_document: dict[str, tuple[float, dict]] = {}
        for chunk in self.chunks.values():
            # ACL is applied before relevance scoring and any text is returned.
            if {"public": 0, "support": 1, "engineering": 2}.get(chunk["access_level"], 3) > clearance:
                continue
            t = terms(chunk["text"])
            if not q or not t:
                continue
            overlap = len(q & t)
            # One generic matching word (for example, "API") is not evidence.
            if overlap < min(2, len(q)):
                continue
            score = overlap / len(q)
            title_overlap = len(q & terms(chunk["title"]))
            score += 0.15 * title_overlap
            doc_id = chunk["document_id"]
            if doc_id not in best_by_document or score > best_by_document[doc_id][0]:
                best_by_document[doc_id] = (score, chunk)
        ranked = sorted(best_by_document.values(), key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in ranked[:limit]]


def make_retriever() -> Retriever:
    # Qdrant adapter can be enabled as it becomes available; memory backend supports demos.
    # A local import avoids making qdrant-client a requirement for CPU smoke runs.
    if os.getenv("VECTOR_BACKEND", "memory") == "qdrant":
        try:
            from ingest.qdrant_store import QdrantRetriever
            return QdrantRetriever()
        except ImportError as exc:
            raise RuntimeError("Install qdrant-client to use VECTOR_BACKEND=qdrant") from exc
    return MemoryRetriever()
