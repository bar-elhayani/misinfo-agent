"""
Run a single MCP call (classify_claim only, no agent loop) on the
evaluation sample. This is evaluation level 2 of 3, testing whether a
single RAG-grounded LLM call - without multi-agent orchestration -
already performs well, as a comparison point for the full agent (level 3).
"""

import sys
import time
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "mcp_server"))

from server import classify_claim

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_SAMPLE_PATH = PROJECT_ROOT / "evaluation" / "eval_sample.csv"
OUTPUT_PATH = PROJECT_ROOT / "evaluation" / "results_single_mcp_call.csv"

# Maps classify_claim's verdict to a binary fake/real label, matching
# WELFake's convention (0 = real, 1 = fake).
# REFUTES -> the article's claim contradicts known facts -> likely fake (1)
# SUPPORTS -> the article's claim matches known facts -> likely real (0)
# NOT ENOUGH INFO -> no clear evidence either way -> default to real (0),
#   a conservative choice that avoids penalizing articles the RAG corpus
#   simply doesn't have coverage for.
VERDICT_TO_LABEL = {
    "REFUTES": 1,
    "SUPPORTS": 0,
    "NOT ENOUGH INFO": 0,
}

eval_df = pd.read_csv(EVAL_SAMPLE_PATH)
print(f"Evaluating on {len(eval_df)} articles")

results = []

for i, row in eval_df.iterrows():
    # Use the title as the "claim" - the article's core assertion, which
    # is what classify_claim is designed to fact-check against FEVER.
    claim_text = str(row["title"])

    start_time = time.time()
    verdict_result = classify_claim(claim_text)
    latency = time.time() - start_time

    predicted_verdict = verdict_result.get("verdict", "NOT ENOUGH INFO")
    predicted_label = VERDICT_TO_LABEL.get(predicted_verdict, 0)

    results.append({
        "article_id": row["article_id"],
        "true_label": row["label"],
        "predicted_verdict": predicted_verdict,
        "predicted_label": predicted_label,
        "confidence": verdict_result.get("confidence", "unknown"),
        "latency_seconds": latency,
    })

    print(f"[{i+1}/{len(eval_df)}] article_id={row['article_id']} -> {predicted_verdict} (true_label={row['label']})")

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_PATH, index=False)

accuracy = (results_df["true_label"] == results_df["predicted_label"]).mean()
avg_latency = results_df["latency_seconds"].mean()

print(f"\nAccuracy on eval sample: {accuracy:.4f}")
print(f"Average latency per article: {avg_latency:.4f} seconds")
print(f"Results saved to: {OUTPUT_PATH}")