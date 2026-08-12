"""
Run the fine-tuned BERT baseline on the evaluation sample (eval_sample.csv).
This is evaluation level 1 of 3 (classical baseline), to be compared against
single MCP call and full multi-agent levels.
"""

import time
import pandas as pd
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification

PROJECT_ROOT = Path(__file__).resolve().parent
EVAL_SAMPLE_PATH = PROJECT_ROOT / "eval_sample.csv"
MODEL_DIR = PROJECT_ROOT / "bert_baseline_model"
OUTPUT_PATH = PROJECT_ROOT / "results_bert_baseline.csv"

MAX_LENGTH = 256

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

# Step 1: Load the fine-tuned model + tokenizer
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR)).to(device)
model.eval()  # inference mode - disables dropout, etc.

# Step 2: Load the evaluation sample
eval_df = pd.read_csv(EVAL_SAMPLE_PATH)
print(f"Evaluating on {len(eval_df)} articles")

# Step 3: Run inference on each article, tracking latency
results = []

for _, row in eval_df.iterrows():
    text = str(row["title"]) + " " + str(row["body_text"])

    start_time = time.time()

    inputs = tokenizer(text, truncation=True, padding="max_length", max_length=MAX_LENGTH, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        predicted_label = torch.argmax(probs, dim=1).item()
        confidence = probs[0][predicted_label].item()

    latency = time.time() - start_time

    results.append({
        "article_id": row["article_id"],
        "true_label": row["label"],
        "predicted_label": predicted_label,
        "confidence": confidence,
        "latency_seconds": latency,
    })

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_PATH, index=False)

# Step 4: Quick summary
accuracy = (results_df["true_label"] == results_df["predicted_label"]).mean()
avg_latency = results_df["latency_seconds"].mean()

print(f"Accuracy on eval sample: {accuracy:.4f}")
print(f"Average latency per article: {avg_latency:.4f} seconds")
print(f"Results saved to: {OUTPUT_PATH}")