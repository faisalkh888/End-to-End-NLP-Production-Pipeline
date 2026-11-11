# Atlas Support AI

Production-oriented reference implementation of an internal product-documentation assistant and support-ticket triage service. It is designed to run locally with one command and to grow into a GPU-backed training and serving system.

> **Status:** reference prototype. A Kaggle-produced SFT LoRA adapter is available as a local serving artifact; the DPO adapter is not selected because its reported reviewed-set scores were substantially lower. Evaluation data is fictional and manually reviewed, so its results are demonstration evidence only, not real-customer acceptance evidence.

## Start locally

### Docker Desktop (recommended)

Install and start [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/), then open a **new** PowerShell terminal so `docker` is available on `PATH`. Confirm the CLI works:

```powershell
docker --version
docker compose version
```

In the repository folder, copy the sample environment file and start the services:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API is at `http://localhost:8000`; interactive docs at `/docs`; health at `/health`. To stop the stack, press `Ctrl+C`, then run `docker compose down`.

### Run the API without Docker

This option runs only the API with the in-memory retrieval backend. In PowerShell, run each line separately:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, skip activation and call the virtual environment's Python directly:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn serving.app:app --reload
```

If activation succeeded, install and start with:

```powershell
pip install -e '.[dev]'
uvicorn serving.app:app --reload
```

The default local mode retrieves indexed documents using lexical scoring and returns an extractive grounded response. To serve QA through vLLM, set `GENERATOR_URL=http://vllm:8000` in `.env`. To serve triage with the SFT LoRA adapter, follow **Serve the SFT adapter** below. vLLM requires NVIDIA Container Toolkit support and enough GPU memory for the base model plus adapter. Set `API_TOKEN` to require bearer authentication (unset means local development authentication is disabled). Docker Compose starts Qdrant and MLflow; set `VECTOR_BACKEND=qdrant` to use Qdrant, otherwise the API uses a local in-memory index.

## Endpoints

- `POST /v1/qa` — `{ "question": "...", "access_level": "public" }`; caller access level must be `public`, `support`, or `engineering`. Returns an answer, citations, and refusal flag.
- `POST /v1/triage` — `{ "ticket": "..." }`; returns schema validated category, priority, product area and summary.
- `POST /v1/admin/reindex` — re-indexes files in `data/docs` (requires auth when configured).
- `GET /metrics`, `GET /health`.

Example:

```sh
curl -X POST http://localhost:8000/v1/qa -H 'Content-Type: application/json' \
  -d '{"question":"How do I reset my API key?","access_level":"public"}'
```

## Architecture

`ingest/` handles document loading, stable chunk IDs, access metadata, incremental upserts and deletion of stale chunks. Qdrant is the configured vector store; the lexical fallback keeps the reference service runnable without downloading model weights. `serving/` exposes FastAPI contracts, authorization, rate limiting, safe prompt construction, optional OpenAI-compatible generation and version headers. Retrieval enforces document ACLs before ranking. `training/` contains reproducible SFT/DPO and encoder baseline entry points, while `evals/` contains metrics, frozen samples and red-team cases. `observability/` provides Prometheus/Grafana assets and weekly category drift reporting. `deploy/` contains Kubernetes starter manifests.

## Data and models

The included docs and ticket/training examples are fictional synthetic samples. `data/docs/` contains 501 Markdown pages with 501 metadata sidecars; `data/processed/` contains 700 synthetic SFT examples, 700 synthetic preference pairs and 700 synthetic retrieval pairs. Regenerate training examples with `python scripts/generate_synthetic_training_data.py`. Do not treat these as production training or evaluation data, and do not claim synthetic preference pairs meet the human-review requirement. The default retrieval mode is lexical, not a dense hybrid index. The optional generator is configured externally through `GENERATOR_URL`; choose a model whose current license permits your usage and record the exact model revision and license in its model card before training or deployment. The training configs default to `Qwen/Qwen2.5-3B-Instruct`; verify its license and hardware requirements before use. No model weights are bundled.

For a standalone GPU training smoke run, import [`kaggle/atlas_support_ai_training.ipynb`](kaggle/atlas_support_ai_training.ipynb) into Kaggle and select a GPU accelerator. It trains synthetic QLoRA SFT and DPO adapters. The reviewed bundle contains the adapters and evaluation reports; the reported SFT metrics were stronger than DPO on the supplied 70 fictional manually reviewed scenarios. These are not real-customer acceptance metrics.

### Serve the SFT adapter

The SFT adapter is stored locally at `models/triage-sft/` and excluded from Git. If that folder is missing, extract only `triage-sft-adapter/` from `atlas_support_ai_reviewed_bundle.zip` into `models/triage-sft/` (the folder should directly contain `adapter_config.json` and `adapter_model.safetensors`). The Compose vLLM service registers it as `atlas-triage-sft`; the API routes only `/v1/triage` to it, while `/v1/qa` continues to use `GENERATOR_URL`. The vLLM 0.5.3 serving copy uses the base Qwen tokenizer: the tokenizer JSON produced by the newer Kaggle training stack is not parseable by this vLLM image, so preserve the training tokenizer separately if you re-extract the bundle.

Set these values in `.env`:

```dotenv
TRIAGE_GENERATOR_URL=http://vllm:8000
TRIAGE_GENERATOR_MODEL=atlas-triage-sft
MODEL_VERSION=atlas-triage-sft
```

Start the GPU profile from the repository folder:

```powershell
docker compose --profile gpu up --build
```

Then, in another PowerShell terminal, evaluate the running API against the reviewed JSONL set:

```powershell
python -m evals.evaluate_triage --dataset evals/data/reviewed_triage.jsonl --endpoint http://localhost:8000 --output evals/results/triage_sft_endpoint.json
```

The triage endpoint uses the SFT training prefix and the OpenAI-compatible completions API so inference matches training more closely. The evaluator saves each successful prediction to `evals/results/triage_sft_endpoint.json.progress.jsonl`, resumes matching completed tickets on rerun, and waits/retries if the API returns HTTP 429. The report includes category, priority, and product-area accuracy, category macro-F1, and JSON validity. Treat it as a measurement on that particular fictional reviewed set. The project pins vLLM 0.5.3, whose Qwen2.5 path cannot use its BitsAndBytes quantizer. It serves the adapter as a standard LoRA against the FP16/BF16 base and uses 2 GB CPU offload, 1 GB swap, a 2048 token context, and eager execution to fit the 6 GB GPU. CPU offload trades inference speed for memory. Since the adapter was trained with QLoRA, compare endpoint metrics with the notebook results and report this runtime difference.

### Latest local evaluation (2026-11-11)

The ZIP (6) SFT adapter was routed through the running vLLM service and compared with the previous installed adapter on the same 70-ticket file, `evals/data/reviewed_triage.jsonl`. The ZIP (6) candidate is the current contents of `models/triage-sft/`; the prior adapter is retained in `models/triage-sft-installed-backup/`.

| Adapter | Category accuracy | Priority accuracy | Product-area accuracy | Category macro-F1 | Valid JSON |
| --- | ---: | ---: | ---: | ---: | ---: |
| Previous installed adapter | 78.6% | 44.3% | 68.6% | 0.736 | 100% |
| ZIP (6) SFT candidate | 88.6% | 60.0% | 81.4% | 0.886 | 100% |

Reports: `evals/results/triage_sft_routed.json` and `evals/results/triage_sft_zip6_routed.json`. These figures describe only the supplied fictional, manually reviewed scenarios; they do not establish production accuracy.

The saved one-user Locust run recorded 81 requests with zero failures (52 `POST /v1/qa`, 29 `POST /v1/triage`). QA median/average latency was 60/47 ms; triage median/average was 4,200/4,228 ms. This is a small, single-user smoke load test, not a capacity result.

A completed four-minute Locust run on 2026-11-11 ramped to 20 users at 2 users/second. The baseline recorded 111 requests, 23 failures (20.7%), and 0.47 requests/second. After bounded triage admission and a marked deterministic fallback, the same run settings recorded 193 requests, zero failures, and 0.82 requests/second. QA p95 was 48 ms; model-backed triage p95 was 7.9 seconds; 55/75 triage requests (73.3%) used `fallback-busy`. Reliability improved by shifting concurrent calls to the deterministic fallback. It scored 24.3% category accuracy, 37.1% priority accuracy, and 27.1% product-area accuracy on the fictional reviewed set, so the change has a substantial quality tradeoff. Fallback scores are in `evals/results/triage_fallback_reviewed.json`. After changing to two vLLM sequences and a 20-second API queue, a fresh four-minute 20-user run completed 175 requests with zero failures: all 66 triage calls used the SFT model, with no fallback. Triage p95 was 17 seconds (average 8.58 seconds); QA p95 was 46 ms. This trades the fallback-heavy run for higher model-backed triage latency. A final repeat after restarting Compose recorded 167 requests, zero failures, and 0.72 requests/second; again, all 66 triage calls used the SFT model. Triage p95 was 15 seconds and QA p95 was 69 ms. Latest report: `evals/results/locust_multiuser_final_report.json`. See `evals/results/locust_multiuser_queue_ready_report.json` and its CSV/HTML artifacts. Compare `evals/results/locust_multiuser_report.json` and `evals/results/locust_multiuser_after_guard_report.json`; CSVs and HTML reports accompany each run. vLLM INFO logs include prompt text, so keep real customer data out until logging is disabled or redacted.

The expanded retrieval evaluation in `evals/data/qa.jsonl` has 27 fictional, documentation-grounded cases. It first scored 0.815 recall@5 (22/27); after adding query normalization from “initial setup” to the corpus wording “getting started” in `serving/retrieval.py`, it scored 1.0 (27/27) on the same set. Because that set exposed the exact phrase used to tune retrieval, this is a development result, not independent evidence of generalization.

A separate 20-case set in `evals/data/qa_holdout.jsonl` scored 0.95 recall@5 (19/20) before singular/plural normalization was added for “permission”/“permissions”; it scored 1.0 (20/20) after. The previously missed Automation permissions query now retrieves the permissions page. The follow-up result is a development check on the set used to diagnose this mismatch, not independent evidence. Both retrieval sets are generated from synthetic page templates and checked against target Markdown procedures and metadata; they are not independent real-user queries. The answer-and-citation evaluation below is also synthetic. An untouched, human-authored holdout, answer-faithfulness adjudication, and a full security/operational review remain before any production claim.

The endpoint answer-and-citation development check is in `evals/data/qa_answer_eval.jsonl`. Before the fallback-selection fix, it exactly matched the reference procedure in 8/20 cases (40%), cited the expected document in 14/20 (70%), and did both in 8/20 (40%); it refused 6 cases. After lowering the redundant passage cutoff and scoring procedure sentences above headings, it matched both answer text and citation in 19/20 cases (95%). Subsequent query normalization maps “permission” to “permissions,” troubleshooting paraphrases (such as “diagnose an issue” or “work through a problem”) to “troubleshooting,” “setup options” to “configuration,” and edit/change-setting wording to “configuration.” The targeted Automation permission query now returns the correct section and citation. The final authenticated engineering-clearance run used the evaluator's isolated in-process mode and achieved 20/20 exact answers, 20/20 expected citations, and 20/20 joint success (`evals/results/qa_answer_eval_final.json`). The earlier unauthenticated run returned 85% because three expected Getting Started pages are engineering-only; the live Compose API is intentionally public-only while `API_TOKEN` is unset. Do not lower document ACLs to improve the score.

The six-case development set in `evals/data/qa_answer_dev.jsonl` covers these previously observed wording gaps. It scored 100% exact reference-answer match and 100% citation support when equivalent template pages are accepted; exact document-ID match was 5/6 because the corpus contains identical sibling pages. See `evals/results/qa_answer_dev.json`. The 20-case file `evals/data/qa_answer_holdout.jsonl` initially scored 75% exact answers, 70% exact expected document IDs, and 65% joint success, with 3 refusals. Its failures were then used to construct the development set, so treat that holdout as consumed rather than independent evidence. All these examples are fictional and template-derived. `GENERATOR_URL` is unset, so these figures evaluate the extractive fallback, not generated answer quality. Create a new untouched, human-authored holdout before making broader quality claims.

A separate 20-question public-access challenge set, `evals/data/qa_answer_challenge.jsonl`, currently scores 100% exact reference-answer match, 100% accepted citation match, and 100% exact expected-document ID match; see `evals/results/qa_answer_challenge.json`. It covers configuration, limits, permissions, and troubleshooting pages across the synthetic product areas. Getting Started pages are intentionally excluded because the corpus marks them support/engineering-only and the local public QA endpoint correctly refuses public access. This challenge set uses the same templated corpus procedures and is a smoke check, not an independent or human acceptance evaluation. Keep its score separate from the older consumed holdout.

## Operations

- Put secrets in environment variables or a secret manager; never commit `.env`.
- Restrict `access_level` based on the authenticated identity in a real deployment. The sample maps bearer auth to one configured caller level; it is not a full identity provider.
- Configure rate limits, request size, retention and TLS at the gateway in production.
- Prometheus scrapes `/metrics`; import `observability/grafana-dashboard.json` into Grafana.
- Training uses MLflow tracking (`MLFLOW_TRACKING_URI`) and DVC (`dvc repro`). Promotion workflow runs frozen regression checks. Update registry aliases only after full evaluation.
- `docs/MODEL_CARD_TRIAGE.md`, `docs/MODEL_CARD_RAG.md`, `docs/EVALUATION_REPORT.md` and `docs/ROADMAP.md` describe limitations and evidence requirements.
- Run `python -m evals.evaluate_triage --dataset evals/data/reviewed_triage.jsonl --endpoint http://localhost:8000 --output evals/results/triage_sft_endpoint.json` against the running SFT candidate to create triage metrics. Use representative reviewed data for any promotion decision.
- Run `python -m evals.run_redteam --endpoint http://localhost:8000 --output evals/results/redteam_local.json` for the local prompt-injection, PII/credential, ticket-jailbreak, bearer-auth and ACL smoke checks. This is not a penetration test or production security certification. If `API_TOKEN` is unset, the Compose API is anonymous and grants public clearance only; set a real secret and identity-aware authorization before exposing it beyond local development.
- Under concurrent load, triage may use a deterministic fallback marked by `X-Triage-Mode: fallback-*`; monitor `atlas_triage_fallback_total` and evaluate fallback quality before relying on these results.

## Development

```sh
pip install -e '.[dev,train]'
python -m ingest.index --source data/docs
python -m evals.run --dataset evals/data/qa.jsonl
```

See `docs/ARCHITECTURE.md` for data flow and `docs/DEMO_SCRIPT.md` for a 10-minute walkthrough. The project includes tests and CI definitions; run `pytest` locally before submitting changes.


### Final frozen QA check (2026-11-11)

After freezing the retrieval code, I authored a separate 20-question public-access set in `evals/data/qa_answer_final_holdout.jsonl`, checked each reference answer against its named Markdown source, and evaluated the running Compose API. It scored 75% exact normalized answer support (15/20), 95% accepted citation match (19/20), 70% exact document-ID match (14/20), and 75% joint answer-and-citation success (15/20), with one refusal and zero HTTP errors. Detailed report: `evals/results/qa_answer_final_holdout.json`. The same-area acceptable citation list accounts for repeated synthetic pages containing identical guidance, so exact-ID score is separate. This set was not used for retrieval changes after evaluation. The corpus and questions are synthetic and source-checked, not user-reviewed acceptance evidence. Do not tune against this final set; create another frozen set after any future retrieval change. Reproduce with `python -m evals.evaluate_qa_answers --dataset evals/data/qa_answer_final_holdout.jsonl --endpoint http://localhost:8000 --output evals/results/qa_answer_final_holdout.json`.
#   E n d - t o - E n d - N L P - P r o d u c t i o n - P i p e l i n e  
 