Place frozen champion and candidate metrics here in CI. No measured model evaluation is included in this starter repository; do not substitute synthetic demo scores for production promotion evidence.


## Final QA answer-and-citation check

`qa_answer_eval_final.json` is the latest 20-question evaluation. It used the in-process FastAPI application with an isolated evaluation token and engineering caller clearance, resulting in 20/20 exact answer matches and 20/20 expected citation matches. The anonymous live Compose endpoint is public-only while `API_TOKEN` is unset, so its earlier 17/20 result omitted three ACL-restricted Getting Started pages. Keep those pages restricted; do not compare anonymous and engineering-clearance metrics as if they were the same access condition. Reproduce with `python -m evals.evaluate_qa_answers --dataset evals/data/qa_answer_eval.jsonl --in-process --caller-access-level engineering --output evals/results/qa_answer_eval_final.json`. The set is synthetic and does not establish real-user answer quality.


## Fresh QA holdout (2026-11-11)

`qa_answer_fresh_holdout_2026-11-11.json` is the report for a newly authored 20-question procedural/safety/limits set, run in-process with engineering clearance. Scores: answer support 60%, expected citation match 85%, exact document ID 60%, joint answer-and-citation 55%, 2 refusals, 0 HTTP errors. Its source answers are checked against the synthetic Markdown corpus. No retrieval tuning was performed after this run. Because duplicate pages repeat guidance, acceptable citations are restricted to accessible documents in the same product area that contain the gold answer; exact-ID score is shown separately. This is prototype-only evidence. Dataset: `../data/qa_answer_fresh_holdout_2026-11-11.jsonl`.


## QA retrieval tuning (2026-11-11)

The 12-question procedural development baseline is `qa_answer_development_baseline_2026-11-11.json` (answer 66.7%, citation 83.3%, exact ID 58.3%, joint 66.7%). After tuning extractive sentence ranking, the in-process result is `qa_answer_development_tuned_2026-11-11.json` and the live Compose API result is `qa_answer_development_live_2026-11-11.json` (both: answer 91.7%, citation 100%, exact ID 66.7%, joint 91.7%, zero refusals/errors). The original 20-question fresh-set result remains the pre-change score in `qa_answer_fresh_holdout_2026-11-11.json`; its failures were inspected, so it is no longer a blind holdout. Freeze code before building a new untouched final set. These synthetic exact-match measures are development signals, not human acceptance evidence.
