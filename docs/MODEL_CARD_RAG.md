# System card: Atlas documentation QA

## Status and intended use

Reference RAG system for answering product support questions from approved documentation with citations. Not an authority for contractual terms, security response, or customer-specific records.

## Data and retrieval

Included corpus is synthetic fictional documentation and is tagged CC0-1.0. Real corpora need per-document source, license, revision, owner and access metadata. The local backend uses lexical overlap. Optional Qdrant backend uses sentence-transformers/all-MiniLM-L6-v2 dense embeddings plus lexical reranking. Verify and record the embedding model license/revision before deployment. ACL filtering precedes result exposure.

## Generation, evaluation and limits

No weights are bundled; `GENERATOR_URL` can point to a separately operated compatible model server. The local fallback quotes retrieved text. No faithfulness or recall result is asserted. Evaluate retrieval recall@5 and human-reviewed faithfulness on frozen, representative questions. Stale documentation, retrieval misses and prompt injection in source pages can affect output; the system delimits retrieved text, cites passages and refuses when retrieval is empty, but generated answers still require adversarial validation.
