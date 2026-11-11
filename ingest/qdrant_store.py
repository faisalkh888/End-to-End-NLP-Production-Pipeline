"""Qdrant dense-vector backend. Dense + lexical reciprocal-rank fusion is used at query time."""
import hashlib
import json
import os
import re
from pathlib import Path

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from ingest.chunking import chunk_document


class QdrantRetriever:
    def __init__(self):
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.collection = os.getenv("QDRANT_COLLECTION", "atlas_docs")
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(self.collection, vectors_config=models.VectorParams(
                size=self.encoder.get_sentence_embedding_dimension(), distance=models.Distance.COSINE))

    def index_directory(self, source: Path) -> int:
        points, live = [], set()
        for file in sorted(source.rglob("*.md")):
            meta_path = file.with_suffix(".json")
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            doc = {"document_id": meta.get("document_id", file.stem), "title": meta.get("title", file.stem),
                   "access_level": meta.get("access_level", "public"), "text": file.read_text(encoding="utf-8")}
            for chunk in chunk_document(doc):
                live.add(chunk["chunk_id"])
                point_id = hashlib.md5(chunk["chunk_id"].encode()).hexdigest()
                points.append(models.PointStruct(id=point_id, vector=self.encoder.encode(chunk["text"]).tolist(),
                                                 payload=chunk))
        if points:
            self.client.upsert(self.collection, points=points, wait=True)
        # Remove stale chunks for safe incremental re-indexing.
        self.client.delete(self.collection, points_selector=models.FilterSelector(
            filter=models.Filter(must_not=[models.FieldCondition(key="chunk_id", match=models.MatchAny(any=list(live))) ])), wait=True)
        return len(points)

    def search(self, query: str, access_level: str, limit: int = 5) -> list[dict]:
        level = {"public": 0, "support": 1, "engineering": 2}.get(access_level, 0)
        allowed = ["public"] + (["support"] if level >= 1 else []) + (["engineering"] if level >= 2 else [])
        vector = self.encoder.encode(query).tolist()
        dense = self.client.query_points(self.collection, query=vector, limit=limit * 3,
            query_filter=models.Filter(must=[models.FieldCondition(key="access_level", match=models.MatchAny(any=allowed))])).points
        qterms = set(re.findall(r"[a-z0-9]+", query.lower()))
        # Lightweight lexical rerank fused with dense rank. ACL filtering already occurred server-side.
        ranked = []
        for rank, point in enumerate(dense, 1):
            p = point.payload
            overlap = len(qterms & set(re.findall(r"[a-z0-9]+", p["text"].lower()))) / max(1, len(qterms))
            ranked.append((1 / (60 + rank) + overlap / 60, p))
        return [p for _, p in sorted(ranked, key=lambda x: x[0], reverse=True)[:limit]]
