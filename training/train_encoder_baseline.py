"""Train a light sentence-transformer retrieval baseline from labeled query/passages."""
import json
from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

rows = [json.loads(x) for x in open("data/processed/retrieval_pairs.jsonl", encoding="utf-8")]
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
examples = [InputExample(texts=[x["query"], x["positive"]]) for x in rows]
model.fit(train_objectives=[(DataLoader(examples, shuffle=True, batch_size=16), losses.MultipleNegativesRankingLoss(model))],
          epochs=1, output_path="models/retriever")
