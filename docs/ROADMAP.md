# Acceptance evidence and implementation roadmap

This repository is a demonstrable resume project, not a claim that the capstone's measured acceptance criteria have been achieved. The current included corpus is 501 synthetic pages, with synthetic training examples and preference pairs; these are illustrative only. No trained model, human-reviewed preference set, judge scores, load report, or demo recording is supplied.

| Requirement | Current state | Evidence required before calling complete |
|---|---|---|
| 500+ indexed pages and incremental indexing | 501 synthetic Markdown pages with sidecar metadata, stable IDs and stale cleanup | Index licensed, reviewed docs; verify updates/deletions against Qdrant |
| Hybrid retrieval and reranking | Optional Qdrant dense retrieval with lexical reranking; lexical memory fallback | Add sparse retrieval and a cross-encoder reranker; report recall@5 >= 0.80 |
| Faithful cited QA | ACL-filtered citations, extractive fallback, optional generator | Frozen human-reviewed QA set and judge/human score >= 0.85 faithfulness |
| QLoRA + DPO | QLoRA/DPO entry points, configs and 700 clearly synthetic examples/pairs | Curated scrubbed dataset; at least 500 human-reviewed preference pairs; GPU run artifacts |
| Triage performance | Schema-valid endpoint, deterministic fallback and endpoint evaluator | Train and compare prompt-only, SFT and DPO on a frozen reviewed holdout; JSON validity >=99%, macro-F1 improvement |
| Auth and rate limiting | Optional bearer token, fixed caller clearance and in-process limit | Identity provider, distributed limiter, TLS and request-size enforcement at ingress |
| Eval/regression gate | Recall@k, macro-F1, JSON validity, Wilson/bootstrap intervals and manual workflow-dispatch champion/candidate gate | Add calibrated answer faithfulness judging; populate complete metrics from repeatable jobs and test deliberate regressions |
| Red team | Injection, restricted docs, PII, jailbreak cases | Execute cases against deployed candidate and attach results; verify zero restricted leakage |
| MLOps | DVC stages, MLflow config, alias promotion helper | Remote DVC storage, registered models, permissions, artifacts and rollback rehearsal |
| Monitoring | Prometheus request counters/latency histogram, estimated input tokens and Grafana dashboard | Add streaming TTFT/output tokens, run 20-user load test, and schedule weekly drift reporting |
| Deployment | Docker Compose, non-root API container, Kubernetes starter | Build image, integration smoke test, secrets and cluster hardening |

Known implementation gaps: Compose's `env_file` expects `.env`; the optional vLLM profile needs a compatible GPU host and licensed model access; the Qdrant collection initializer downloads its encoder on first use; only API container runs non-root by default; rate limiting is process-local; token counts are estimates; non-streaming generation means true TTFT is not currently measured. The DPO trainer refuses synthetic pairs by default. Follow the acceptance evidence column before presenting this as production complete.
