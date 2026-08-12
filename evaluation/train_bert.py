"""
Fine-tune a BERT classifier on WELFake articles (title + body text) to
serve as a strong classical ML baseline, for comparison against the
single MCP call and full multi-agent evaluation levels.

Critical: articles used in the evaluation sample (eval_sample.csv) are
excluded from training, to avoid the model being tested on data it has
already seen.
"""

import duckdb
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "misinfo.duckdb")
EVAL_SAMPLE_PATH = PROJECT_ROOT / "evaluation" / "eval_sample.csv"
MODEL_OUTPUT_DIR = PROJECT_ROOT / "evaluation" / "bert_baseline_model"

TRAIN_SIZE = 8000
RANDOM_SEED = 42

# Step 1: Load the eval sample's article_ids, so we can exclude them from training
eval_sample = pd.read_csv(EVAL_SAMPLE_PATH)
eval_article_ids = set(eval_sample["article_id"])
print(f"Excluding {len(eval_article_ids)} article_ids used in the evaluation sample")

# Step 2: Load all articles from mart_articles, excluding the eval sample
con = duckdb.connect(DB_PATH, read_only=True)
all_articles = con.execute("SELECT article_id, title, body_text, label FROM mart_articles").fetchdf()
con.close()

train_pool = all_articles[~all_articles["article_id"].isin(eval_article_ids)]
print(f"Training pool available: {len(train_pool)} articles (after excluding eval sample)")

# Step 3: Sample a balanced training set
train_df = train_pool.sample(n=min(TRAIN_SIZE, len(train_pool)), random_state=RANDOM_SEED)
print(f"Training set: {len(train_df)} articles ({(train_df['label'] == 1).sum()} fake, {(train_df['label'] == 0).sum()} real)")

import torch
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from datasets import Dataset

MODEL_NAME = "bert-base-uncased"
MAX_LENGTH = 256  # tokens - truncates long articles, keeps training fast

# Step 4: Split into train/validation
train_split, val_split = train_test_split(
    train_df, test_size=0.1, random_state=RANDOM_SEED, stratify=train_df["label"]
)
print(f"Train: {len(train_split)}, Validation: {len(val_split)}")

# Step 5: Combine title + body into a single text field
# (BERT takes one text input per example - concatenating gives it both signals)
train_split = train_split.copy()
val_split = val_split.copy()
train_split["text"] = train_split["title"].fillna("") + " " + train_split["body_text"].fillna("")
val_split["text"] = val_split["title"].fillna("") + " " + val_split["body_text"].fillna("")

# Step 6: Tokenize
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_fn(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=MAX_LENGTH)

train_dataset = Dataset.from_pandas(train_split[["text", "label"]].rename(columns={"label": "labels"}))
val_dataset = Dataset.from_pandas(val_split[["text", "label"]].rename(columns={"label": "labels"}))

train_dataset = train_dataset.map(tokenize_fn, batched=True)
val_dataset = val_dataset.map(tokenize_fn, batched=True)

print("Tokenization complete")
print(train_dataset)

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

# Step 7: Load the pretrained model with a classification head
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

# Step 8: Define how to compute metrics during training
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "f1": f1_score(labels, predictions),
    }

# Step 9: Training configuration
training_args = TrainingArguments(
    output_dir=str(PROJECT_ROOT / "evaluation" / "bert_checkpoints"),
    num_train_epochs=2,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    eval_strategy="epoch",
    save_strategy="no",  # we'll save the final model manually - no need for intermediate checkpoints
    logging_steps=50,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
)

# Step 10: Train
print("Starting training...")
trainer.train()

# Step 11: Save the final fine-tuned model + tokenizer
MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
trainer.save_model(str(MODEL_OUTPUT_DIR))
tokenizer.save_pretrained(str(MODEL_OUTPUT_DIR))
print(f"Model saved to: {MODEL_OUTPUT_DIR}")