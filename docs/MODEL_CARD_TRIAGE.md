# Model card: Atlas ticket triage

## Status

Prototype. A Kaggle-produced Qwen2.5-3B-Instruct LoRA SFT adapter is available in the reviewed training bundle and can be served through the optional vLLM Compose profile. The reported DPO adapter scored substantially lower on the supplied reviewed set and is not selected. The endpoint otherwise uses the deterministic keyword fallback if no generator is configured or the generator returns no valid response.

## Intended use

Suggest category, priority, product area and a concise summary for human-reviewed support routing. It must not decide account actions, security incident severity, refunds or customer eligibility autonomously.

## Data and training

Training scripts target Qwen2.5-3B-Instruct with 4-bit LoRA SFT followed by DPO. This is a configuration, not a completed training run. Only use consented, licensed ticket data. The preparation script masks common email, phone and token patterns; review residual PII before training. DPO needs at least 500 human-reviewed preference pairs. Record source, license, consent, split IDs and model revision with each run.

## Evaluation and limitations

The provided SFT comparison was run on 70 fictional manually reviewed scenarios; it is demonstration evidence, not real-customer acceptance evidence. Re-evaluate the adapter through `/v1/triage` using `evals/evaluate_triage.py` before considering promotion. The endpoint report includes category macro-F1, category/priority/product-area accuracy, and JSON validity. Rare categories, multilingual tickets, sarcasm and unseen product areas may be misclassified. Require human review and a safe escalation path.
