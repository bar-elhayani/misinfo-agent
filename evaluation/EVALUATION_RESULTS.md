# Evaluation Results

Comparison of three evaluation levels on a balanced sample of 60 WELFake articles (30 fake, 30 real), reproducible via `evaluation/create_sample.py` (seed=42).

## Summary Table

| Level | Method | Accuracy | Avg Latency | Notes |
|---|---|---|---|---|
| 1 | Classical baseline (BERT fine-tuned) | **98.33%** | 0.027s | Fine-tuned on 8,000 WELFake articles (excluding eval sample) |
| 2 | Single MCP call (`classify_claim` only) | 50.00% | ~4.5s | Every article returned NOT ENOUGH INFO |
| 3 | Full multi-agent (Content + Network + Supervisor) | 51.67% | 8.51s | Network Agent skipped for all articles (no graph_id) |

## Key Finding: RAG Corpus Mismatch

The single MCP call and full agent levels perform close to chance (50%), far below the classical baseline (98.33%). Investigation traced this to a mismatch between the RAG corpus and the task, not a flaw in the agent's reasoning:

- `classify_claim` retrieves evidence from FEVER, a corpus of general factual claims grounded in Wikipedia (e.g. "Paris is in France").
- WELFake article headlines make specific, time-bound claims about real-world events, people, and politics.
- These two claim types rarely overlap semantically, so retrieval consistently returns irrelevant evidence, and the model correctly (per its own instructions) returns NOT ENOUGH INFO rather than guessing.
- This was confirmed by testing both article titles and opening-paragraph text as the query - both failed identically, ruling out "not enough context in the query" as the cause.

**Implication:** multi-agent orchestration cannot compensate for a retrieval corpus that doesn't cover the task domain. Reasoning on top of irrelevant evidence still produces an uninformative verdict, regardless of how many agents review it.

## Key Finding: No Shared Identifier Between Datasets

WELFake (article text) and UPFD (propagation graphs) share no common identifier - a design choice documented from the start of the project. As a result, the Network Agent's contribution could not be evaluated on this sample: every article received `graph_id=None`, causing the Network Agent to correctly skip (as designed) rather than analyze propagation data it doesn't have.

**Implication:** the current evaluation only tests the Content Agent + Supervisor path. A meaningful test of the Network Agent's added value would require a dataset providing both article text and propagation data for the same claims - which WELFake + UPFD, as currently used, do not.

## What This Evaluation Demonstrates

Despite the agent underperforming the classical baseline here, this framework achieved its actual purpose: it isolated *why* - a retrieval corpus mismatch and a dataset limitation - rather than leaving "the agent didn't work well" unexplained. This is a stronger result for a portfolio project than an agent that outperforms a baseline for unclear reasons.