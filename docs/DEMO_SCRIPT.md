# 10-minute demo walkthrough

1. **0:00–1:00** Explain the support problem and trust boundaries using `docs/ARCHITECTURE.md`.
2. **1:00–2:00** Run `docker compose up --build`; show API health and Qdrant/MLflow services.
3. **2:00–3:00** Show the 500 synthetic demo pages and metadata, then call `POST /v1/admin/reindex`.
4. **3:00–4:30** Ask a documentation question; inspect citation IDs. Ask an unrelated question and show the refusal behavior when no passage matches.
5. **4:30–5:30** Submit tickets for billing and a bug; show the structured triage JSON and model-version header.
6. **5:30–6:30** Demonstrate public ACL filtering using a request that asks for engineering material; verify no restricted citation is returned.
7. **6:30–7:30** Walk through QLoRA and DPO configs, MLflow run tracking and the minimum 500-pair validation.
8. **7:30–8:30** Show evaluation metrics, red-team cases and the candidate/champion regression gate. Use a deliberately lowered candidate metric and demonstrate the blocked status.
9. **8:30–9:30** Show Prometheus metrics, Grafana dashboard and weekly drift report input/output.
10. **9:30–10:00** State measured results, limitations, planned production evidence and rollback through the MLflow champion alias.

Do not imply training, acceptance thresholds or load tests have passed unless you have run and recorded them.
