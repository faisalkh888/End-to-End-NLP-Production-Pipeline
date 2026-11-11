# Atlas Support AI — 10-Minute Demo Recording Guide

**Purpose:** a practical recording plan for the capstone demo deliverable. Commands are written for PowerShell from the repository root. The guide distinguishes features that can be demonstrated now from promotion steps that are not yet proven end to end.

## Important honesty note about CI promotion

The GitHub Actions workflow at `.github/workflows/ci.yml` runs unit tests and retrieval evaluation on pushes and pull requests. Its manually dispatched `promotion-regression` job compares metric JSON provided as workflow inputs. The separate `evals/registry_promote.py` script changes MLflow aliases; the GitHub workflow does **not** call that script. Also, the current QA evaluator reports `answer_exact_support_rate`, not the `faithfulness` field required by the promotion gate.

Therefore, the current project can demonstrate CI checks and a **deliberately blocked regression-gate run**, but the repository evidence does not establish a successful, real-metric CI-to-MLflow promotion. Do not enter invented scores and describe them as measured results. To claim a successful promotion, first wire the CI gate to a real evaluation artifact, register the candidate, and have the passing workflow perform the alias change with auditable credentials.

## 1. Prepare the project

### 1.1 Open the repository in VS Code

Open the folder:

```text
C:\Users\faisa\OneDrive\Documents\ChatGPT\End-to-End NLP Production Pipeline
```

Open a new PowerShell terminal in that folder. Confirm the current directory and Docker CLI:

```powershell
Get-Location
docker --version
docker compose version
```

Expected: the current directory ends with `End-to-End NLP Production Pipeline`, and both Docker commands print versions. If `docker` is not recognized, start Docker Desktop, then open a new VS Code terminal.

### 1.2 Create `.env` only if it does not exist

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Do not open `.env` during recording and do not show tokens, passwords, or private environment values. For SFT triage, the local `.env` should already contain the settings described in the README (`TRIAGE_GENERATOR_URL`, `TRIAGE_GENERATOR_MODEL`, and `MODEL_VERSION`). If you need to edit it, do that before recording and keep the values private.

### 1.3 Start the Compose services, including GPU vLLM

```powershell
docker compose --profile gpu up --build -d
```

Inspect service status:

```powershell
docker compose --profile gpu ps
```

Wait for API health:

```powershell
$apiReady = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        $health = Invoke-RestMethod http://localhost:8000/health -TimeoutSec 3
        if ($health.status -eq 'ok') { $apiReady = $true; break }
    } catch { }
    Start-Sleep -Seconds 5
}
if ($apiReady) { $health } else { docker compose --profile gpu logs --tail 80 api vllm }
```

The base model may take several minutes to load the first time. Confirm the vLLM model alias:

```powershell
(Invoke-RestMethod http://localhost:8001/v1/models).data | Select-Object id
```

Expected model IDs include `Qwen/Qwen2.5-3B-Instruct` and `atlas-triage-sft`. If the alias is not listed, inspect the service log:

```powershell
docker compose --profile gpu logs --tail 100 vllm
```

Do not start recording until model loading is complete and the test requests work. For the standard CPU/API-only demo, `docker compose up --build -d` is enough to show QA, but SFT-backed triage requires the GPU profile.

### 1.4 Open the pages you will show

Open these URLs in Edge before starting the recording:

- Swagger API docs: `http://localhost:8000/docs`
- Atlas project homepage: `http://localhost:8000/`
- Grafana: `http://localhost:3000`
- Prometheus (optional): `http://localhost:9090`
- GitHub repository **Actions** page: open the correct repository in GitHub and select **Actions**.

In Grafana, navigate to **Dashboards → Atlas → Atlas Support AI**. If the dashboard is empty, send a few QA and triage requests, wait for a Prometheus scrape interval, then refresh.

## 2. Prepare the browser/API examples

Use Swagger to avoid shell quoting problems. If using PowerShell instead, these commands send the same example requests.

### 2.1 Show ingestion/reindexing

First show that the fictional documentation and metadata exist:

```powershell
Get-ChildItem data/docs -Filter *.md | Measure-Object
Get-ChildItem data/docs -Filter *.json | Measure-Object
```

The repository contains 501 Markdown pages and matching metadata sidecars. Reindex the current directory through the API:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/admin/reindex | ConvertTo-Json -Depth 5
```

The response should include `updated_chunks`. This demonstrates indexing/reindexing code on the included synthetic corpus; it does not prove a production-grade vector database deployment or real documentation ingestion.

### 2.2 Show a QA request and citation

PowerShell option:

```powershell
$qaBody = @{
    question = 'Where should API credentials be stored?'
    access_level = 'public'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/qa -ContentType 'application/json' -Body $qaBody | ConvertTo-Json -Depth 8
```

Swagger option:

1. On `/docs`, expand **POST `/v1/qa`**.
2. Click **Try it out**.
3. Use this body:

```json
{
  "question": "Where should API credentials be stored?",
  "access_level": "public"
}
```

4. Click **Execute**.
5. Point out the answer, citation/document ID, and `refused` field in the response.

### 2.3 Show a triage request

PowerShell option:

```powershell
$triageBody = @{ ticket = 'The export job crashes every time I select CSV.' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/triage -ContentType 'application/json' -Body $triageBody | ConvertTo-Json -Depth 5
```

Swagger option:

1. Expand **POST `/v1/triage`** and click **Try it out**.
2. Enter:

```json
{
  "ticket": "The export job crashes every time I select CSV."
}
```

3. Click **Execute**.
4. Point out the category, priority, product area, summary, and response model-version header if visible.

Model outputs can vary slightly between runtime sessions. The point is to show a valid structured response, not to promise that this sample ticket always receives one specific label.

### 2.4 Populate monitoring charts

Send several requests with the examples above, or run these PowerShell requests a few times. The following loop sends ten QA requests and three triage requests:

```powershell
1..10 | ForEach-Object {
    $body = @{ question = 'Where should API credentials be stored?'; access_level = 'public' } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/qa -ContentType 'application/json' -Body $body | Out-Null
}
1..3 | ForEach-Object {
    $body = @{ ticket = 'The export job crashes every time I select CSV.' } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/triage -ContentType 'application/json' -Body $body | Out-Null
}
```

Then open Grafana and show latency, throughput, error, and estimated-token panels. Explain that estimated token counts are estimates and the non-streaming API does not report true TTFT.

## 3. Show CI and the regression gate honestly

### 3.1 Show the automatic CI run

1. Open the GitHub repository in Edge.
2. Select **Actions**.
3. Open a successful `quality-and-promotion-gate` run triggered by a push or pull request.
4. Show the `checks` job steps: install development dependencies, run `pytest -q`, and run the retrieval evaluation.
5. Say: “This workflow runs the code/test checks and the retrieval smoke evaluation. The promotion job is separately dispatched and compares submitted metrics.”

If there is no successful run in GitHub yet, don’t claim there is one. You can show `.github/workflows/ci.yml` in VS Code, but explain that a source file is not evidence of a completed CI run.

### 3.2 Demonstrate a deliberately blocked candidate

The manual workflow requires candidate and champion metric JSON. To demonstrate that the gate blocks a regression, use the following **test-only values** in GitHub Actions. They are intentionally below the configured floors and are not project measurements:

Candidate input:

```json
{"recall_at_5":0.79,"faithfulness":0.80,"triage_json_validity":0.98}
```

Champion input:

```json
{"recall_at_5":0.80,"faithfulness":0.85,"triage_json_validity":0.99}
```

Steps:

1. In **Actions**, select `quality-and-promotion-gate`.
2. Click **Run workflow**.
3. Enter the candidate and champion JSON above in the corresponding inputs.
4. Start the workflow and open the `promotion-regression` job.
5. Show that it reports `BLOCK` and exits nonzero.
6. Explain that this proves the regression gate rejects a bad candidate; it does **not** prove a model promotion happened.

### 3.3 What is still needed to show a real promotion

The current gate expects a `faithfulness` metric, but current QA results report `answer_exact_support_rate`. Do not relabel exact answer matching as faithfulness. Before showing an actual promotion:

1. Add a defensible faithfulness evaluator and a repeatable evaluation artifact.
2. Have the workflow consume that artifact rather than user-entered scores.
3. Register the candidate in MLflow and configure the workflow to promote the alias only after the gate passes.
4. Store MLflow credentials as GitHub Actions secrets; never place them in the notebook, recording, or repository.
5. Verify a passing run changed the alias, and record the prior alias/version so rollback can be demonstrated.

Until those steps are complete, describe the promotion flow as **partially implemented** and show the deliberate block instead of claiming successful promotion.

## 4. Recording setup

### Option A: Windows Snipping Tool

1. Open Snipping Tool from the Start menu.
2. Select the **Record** mode (video camera icon), then **New**.
3. Drag to select the screen area that contains VS Code/browser content without exposing private notifications.
4. Click **Start**, record the walkthrough, then click **Stop**.
5. Save the recording as `atlas-support-ai-demo.mp4` in a demo-output folder outside any secrets or data directories.

If your Snipping Tool does not have recording, use OBS Studio: add a **Display Capture** source, select the correct monitor, start recording, then stop and save as MP4. Make a 20-second test first to check the audio and screen capture.

Before recording, close unrelated browser tabs, mute notifications, increase browser zoom enough to read the response, and keep the terminal font large. Never show `.env`, tokens, private datasets, or personal account details.

## 5. Ten-minute walkthrough and suggested narration

| Time | Show | Suggested narration |
|---|---|---|
| 0:00–0:50 | README title and project overview | “Atlas Support AI is a fictional software-company support assistant. It combines document QA and ticket triage. This is a prototype using synthetic documents and evaluation scenarios.” |
| 0:50–2:15 | Homepage, then `data/docs/`, a Markdown page and its JSON metadata; run reindex command | “The homepage provides a simple way to try both endpoints. Each synthetic document has metadata including its ID and access level. The ingestion endpoint chunks and reindexes the folder. The corpus has 501 example pages.” |
| 2:15–3:45 | Homepage QA form or Swagger `POST /v1/qa` response | “The QA endpoint retrieves accessible evidence and returns a cited answer or refusal. Here the citation points back to the documentation source.” |
| 3:45–5:00 | Homepage triage form or Swagger `POST /v1/triage` response | “The triage endpoint uses the SFT LoRA adapter served through vLLM and returns schema-validated JSON: category, priority, product area, and summary.” |
| 5:00–6:15 | Kaggle reviewed notebook and adapter comparison table/report | “I trained SFT and DPO adapters on synthetic examples and compared both on the same 70 fictional reviewed scenarios. SFT was the better candidate; DPO was not selected.” |
| 6:15–7:35 | GitHub Actions successful CI run, then manual blocked gate run | “CI runs tests and retrieval checks. The manual gate blocks candidates below configured floors. This run is an intentional rejection test, not a model promotion. A real CI-to-MLflow promotion is still integration work.” |
| 7:35–8:45 | Grafana Atlas dashboard after generating requests | “Prometheus scrapes service metrics and Grafana displays latency, throughput, errors, and estimated input tokens. This API is non-streaming, so these charts do not measure TTFT.” |
| 8:45–9:35 | `evals/results/` summaries or `docs/PROJECT_REPORT.md` | “The final local 20-user run completed 167 requests with zero failures; SFT triage p95 was 15 seconds. The QA final holdout exact answer-support score was 75%. These are prototype measurements, not production acceptance.” |
| 9:35–10:00 | README limitations | “The documents and test scenarios are synthetic. Before production use, the system needs approved real documentation, independent evaluation, stronger identity/security integration, a verified promotion workflow, and further latency work.” |

Keep the whole recording to approximately 10 minutes. If a request is slow, do not wait silently; narrate what is happening. If a service fails, stop, fix it, and re-record the affected section rather than hiding the failure in editing.

## 6. After recording

1. Watch the MP4 from beginning to end.
2. Confirm audio is clear and the text/API responses are readable.
3. Confirm no `.env`, credential, private path, or private data was visible.
4. Confirm the CI segment accurately says “blocked regression test” unless a genuine, measured promotion actually succeeded.
5. Save the video outside tracked source/model data, or upload it to a suitable GitHub release/video host if the file is too large for normal Git.
6. Add a link in the README under a **Demo** heading. Do not commit large videos or model weights directly unless you intentionally use Git LFS or release assets.

## 7. Final pre-record checklist

- [ ] Docker Desktop is running and GPU profile is ready.
- [ ] `/health` returns `status: ok`.
- [ ] `/v1/models` includes `atlas-triage-sft`.
- [ ] Reindex, QA, and triage examples work before recording.
- [ ] Grafana dashboard shows fresh data.
- [ ] A real GitHub Actions check run is available, or the source workflow is labeled as code only.
- [ ] CI segment distinguishes regression rejection from successful model promotion.
- [ ] `.env`, tokens, private notifications, and unrelated personal information are hidden.
- [ ] The narration identifies the project data and evaluation scenarios as synthetic.
- [ ] The recording is reviewed before uploading or linking it.

