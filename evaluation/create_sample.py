"""
Create a small, balanced, reproducible sample from the WELFake mart_articles
table for use across all three evaluation levels (baseline, single MCP call,
full agent). Using the exact same sample ensures a fair comparison - each
method is judged on identical inputs.
"""

import duckdb
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "misinfo.duckdb")
OUTPUT_PATH = PROJECT_ROOT / "evaluation" / "eval_sample.csv"

SAMPLE_SIZE_PER_CLASS = 30  # 30 fake + 30 real = 60 total
RANDOM_SEED = 42

con = duckdb.connect(DB_PATH, read_only=True)

# Fetch full label subsets, then sample in pandas - more reliable than
# DuckDB's reservoir sampling, which showed inconsistent row counts when
# combined with REPEATABLE (likely due to parallel execution).
fake_df = con.execute("SELECT * FROM mart_articles WHERE label = 1").fetchdf()
real_df = con.execute("SELECT * FROM mart_articles WHERE label = 0").fetchdf()
con.close()

fake_sample = fake_df.sample(n=SAMPLE_SIZE_PER_CLASS, random_state=RANDOM_SEED)
real_sample = real_df.sample(n=SAMPLE_SIZE_PER_CLASS, random_state=RANDOM_SEED)

df = pd.concat([fake_sample, real_sample], ignore_index=True)
df.to_csv(OUTPUT_PATH, index=False)

print(f"Sample created: {len(df)} rows ({(df['label'] == 1).sum()} fake, {(df['label'] == 0).sum()} real)")
print(f"Saved to: {OUTPUT_PATH}")