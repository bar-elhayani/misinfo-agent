"""
Run the full multi-agent system (Content Agent -> Network Agent ->
Supervisor) on the evaluation sample. This is evaluation level 3 of 3.

Note: WELFake articles have no associated UPFD graph_id (the two
datasets share no common identifier - see README). Network Agent will
therefore return SKIPPED for every article, and this run measures
whether the full agent (with Content Agent + Supervisor reasoning)
performs at least as well as the single MCP call, even without a
network signal.
"""

import sys
import time
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "agent"))

from supervisor import graph

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_SAMPLE_PATH = PROJECT_ROOT / "evaluation" / "eval_sample.csv"
OUTPUT_PATH = PROJECT_ROOT / "evaluation" / "results_full_agent.csv"

# Maps the Supervisor's final_label to a binary fake/real label, matching
# WELFake's convention (0 = real, 1 = fake).
LABEL_TO_BINARY = {
    "LIKELY MISINFORMATION": 1,
    "LIKELY LEGITIMATE": 0,
    "INCONCLUSIVE": 0,  # conservative default, same choice as level 2
}

eval_df = pd.read_csv(EVAL_SAMPLE_PATH)
print(f"Evaluating on {len(eval_df)} articles")

results = []

for i, row in eval_df.iterrows():
    claim_text = str(row["title"])

    start_time = time.time()
    final_state = graph.invoke({
        "claim_text": claim_text,
        "graph_id": None,
        "content_verdict": None,
        "network_verdict": None,
        "final_verdict": None,
    })
    latency = time.time() - start_time

    final_verdict = final_state.get("final_verdict", {})
    predicted_final_label = final_verdict.get("final_label", "INCONCLUSIVE")
    predicted_label = LABEL_TO_BINARY.get(predicted_final_label, 0)

    results.append({
        "article_id": row["article_id"],
        "true_label": row["label"],
        "content_verdict": final_state.get("content_verdict", {}).get("verdict"),
        "network_verdict": final_state.get("network_verdict", {}).get("assessment"),
        "predicted_final_label": predicted_final_label,
        "predicted_label": predicted_label,
        "confidence": final_verdict.get("confidence", "unknown"),
        "latency_seconds": latency,
    })

    print(f"[{i+1}/{len(eval_df)}] article_id={row['article_id']} -> {predicted_final_label} (true_label={row['label']})")

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_PATH, index=False)

accuracy = (results_df["true_label"] == results_df["predicted_label"]).mean()
avg_latency = results_df["latency_seconds"].mean()

print(f"\nAccuracy on eval sample: {accuracy:.4f}")
print(f"Average latency per article: {avg_latency:.4f} seconds")
print(f"Results saved to: {OUTPUT_PATH}")