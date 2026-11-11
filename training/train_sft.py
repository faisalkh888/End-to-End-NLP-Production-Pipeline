"""QLoRA supervised fine-tuning entry point; requires a CUDA environment and prepared JSONL."""
import json
import os
import yaml
import mlflow
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer


def main():
    cfg = yaml.safe_load(open(os.getenv("CONFIG", "training/configs/sft.yaml"), encoding="utf-8"))
    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA training requires CUDA; use a GPU runner")
    rows = [json.loads(line) for line in open(cfg["dataset"], encoding="utf-8")]
    dataset = Dataset.from_list(rows)
    tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"])
    compute_dtype = getattr(torch, cfg.get("compute_dtype", "float16"))
    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"], quantization_config=BitsAndBytesConfig(
        load_in_4bit=cfg.get("load_in_4bit", True), bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype), device_map="auto")
    lora = LoraConfig(r=cfg["lora"]["r"], lora_alpha=cfg["lora"]["alpha"], lora_dropout=cfg["lora"]["dropout"],
                      target_modules=cfg["lora"]["target_modules"], task_type="CAUSAL_LM")
    args = TrainingArguments(output_dir=cfg["output_dir"], num_train_epochs=cfg["epochs"],
        learning_rate=cfg["learning_rate"], per_device_train_batch_size=1, gradient_accumulation_steps=16,
        logging_steps=10, save_strategy="epoch", report_to="mlflow",
        fp16=compute_dtype == torch.float16, bf16=compute_dtype == torch.bfloat16,
        gradient_checkpointing=True)
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    with mlflow.start_run():
        mlflow.log_params({"base_model": cfg["base_model"], "dataset_rows": len(rows), "method": "QLoRA-SFT"})
        trainer = SFTTrainer(model=model, args=args, train_dataset=dataset, peft_config=lora,
                             processing_class=tokenizer, dataset_text_field="text")
        trainer.train()
        trainer.save_model(cfg["output_dir"])


if __name__ == "__main__":
    main()
