"""DPO alignment entry point over explicit chosen/rejected preference pairs."""
import json
import os
import yaml
import mlflow
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from trl import DPOConfig, DPOTrainer


def main():
    cfg = yaml.safe_load(open(os.getenv("CONFIG", "training/configs/dpo.yaml"), encoding="utf-8"))
    if not torch.cuda.is_available():
        raise RuntimeError("DPO training requires CUDA; use a GPU runner")
    rows = [json.loads(line) for line in open(cfg["dataset"], encoding="utf-8")]
    if len(rows) < 500:
        raise ValueError(f"DPO requires at least 500 reviewed preference pairs; found {len(rows)}")
    if any(row.get("synthetic", False) for row in rows) and os.getenv("ALLOW_SYNTHETIC_DPO") != "true":
        raise ValueError("Synthetic demo pairs cannot support a meaningful DPO run; provide reviewed pairs or explicitly set ALLOW_SYNTHETIC_DPO=true for a non-evidence smoke run")
    compute_dtype = getattr(torch, cfg.get("compute_dtype", "float16"))
    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"], device_map="auto", torch_dtype=compute_dtype)
    if cfg.get("sft_adapter"):
        model = PeftModel.from_pretrained(model, cfg["sft_adapter"], is_trainable=True)
    tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"])
    args = DPOConfig(output_dir=cfg["output_dir"], num_train_epochs=cfg["epochs"],
                     learning_rate=cfg["learning_rate"], beta=cfg["beta"], per_device_train_batch_size=1,
                     max_length=cfg.get("max_length", 2048), fp16=compute_dtype == torch.float16,
                     bf16=compute_dtype == torch.bfloat16, gradient_checkpointing=True)
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    with mlflow.start_run():
        mlflow.log_params({"dataset_pairs": len(rows), "method": "DPO", "beta": cfg["beta"],
                           "synthetic_data": any(row.get("synthetic", False) for row in rows)})
        DPOTrainer(model=model, args=args, train_dataset=Dataset.from_list(rows), processing_class=tokenizer).train()
        model.save_pretrained(cfg["output_dir"])
        tokenizer.save_pretrained(cfg["output_dir"])


if __name__ == "__main__":
    main()
