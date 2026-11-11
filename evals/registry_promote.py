"""Promote a logged MLflow model only after the evaluation gate succeeds."""
import os
import mlflow
from mlflow.tracking import MlflowClient

uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
name = os.getenv("MODEL_REGISTRY_NAME", "atlas-triage")
version = os.environ["CANDIDATE_VERSION"]
client = MlflowClient(tracking_uri=uri)
client.set_registered_model_alias(name, "challenger", version)
if os.getenv("PROMOTION_GATE_PASSED") != "true":
    raise SystemExit("Candidate registered as challenger; champion unchanged because gate is not passed")
client.set_registered_model_alias(name, "champion", version)
print(f"Promoted {name} version {version}; rollback by resetting champion alias")
