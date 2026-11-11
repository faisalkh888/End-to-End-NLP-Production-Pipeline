# Architecture and trust boundaries

```text
Markdown + sidecar ACLs -> loader/chunker -> Qdrant (optional vectors + payload)
                                          -> local lexical index (demo fallback)
API caller -> auth/rate/request controls -> FastAPI -> ACL filter -> retrieve/rerank
                                          -> optional OpenAI-compatible generator -> citations/schema
Tickets -> PII scrub -> reviewed JSONL -> QLoRA SFT -> DPO -> MLflow registry aliases
Frozen evaluation + red-team -> CI promotion gate -> champion/challenger monitoring
```

Access metadata is attached at ingestion. Retrieval compares document clearance to caller clearance before returning any passage. Public callers are always capped to public even if they request engineering access in the request body. In a production deployment, derive clearance from verified identity claims; the sample uses one configured caller clearance. Retrieved text and incoming ticket content remain untrusted data, delimited in prompts. Generation is optional and disabled until an endpoint is configured. Every generated triage object is schema-validated; malformed output falls back to deterministic classification.

## Scaling notes

The memory backend is for local development. The Qdrant backend encodes with `sentence-transformers/all-MiniLM-L6-v2`, applies an ACL filter server-side and combines dense rank with lexical overlap. For production, persist embedding model revision, add sparse-vector retrieval, use true reciprocal rank fusion and a cross-encoder reranker, benchmark with real queries, and move Qdrant behind private network/authentication. The reference Docker setup does not start model weights; add a vLLM deployment for selected licensed weights and set `GENERATOR_URL` to its compatible endpoint.
