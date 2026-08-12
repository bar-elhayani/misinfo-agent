# Misinformation Detection Agent

Agentic misinformation detection system combining LLM reasoning, propagation network analysis, and RAG-based fact-checking. Built with dbt, DuckDB, LangGraph, MCP, and Docker - evaluated against classical ML baselines.

### Data layer (dbt + DuckDB)

Staging → intermediate → marts pipeline over two independent datasets:
- **WELFake** (72,095 articles) - text-based features (`mart_articles`): clickbait signals, length metrics, missing-value flags.
- **UPFD** (5,778 propagation graphs, PolitiFact + GossipCop) - network features (`mart_network_summary`): spread size, amplification flags, node/edge counts.
- Note: WELFake and UPFD are separate datasets with no shared identifier - they represent two independent evidence axes (content vs. propagation), not a joined dataset. See "Project Learnings" below for what this means for the Network Agent's evaluation.

### RAG (Chroma + FEVER)

165,447 fact-checked claims embedded into a persistent Chroma vector store, enabling semantic search against a Wikipedia-grounded fact-check corpus.

### MCP Server

Exposes four tools backed by the marts and the RAG store, served over the real MCP protocol (`streamable-http` transport, not a direct Python import):
- `get_article_features(article_id)` - WELFake article features
- `get_network_summary(graph_id)` - UPFD propagation metrics
- `search_fact_checks(claim_text)` - semantic search over the FEVER corpus
- `classify_claim(claim_text)` - RAG-grounded verdict (SUPPORTS / REFUTES / NOT ENOUGH INFO) via Claude, constrained to retrieved evidence only
- `assess_network_pattern(graph_id)` - LLM-based read of a propagation graph's spread pattern (ORGANIC / SUSPICIOUS / INCONCLUSIVE)

### LangGraph Multi-Agent System

Three agents, each calling the MCP server as a real client over HTTP:
- **Content Agent** - wraps `classify_claim`
- **Network Agent** - wraps `assess_network_pattern`, skips gracefully when no `graph_id` is available
- **Supervisor Agent** - combines both verdicts into a final label, explicitly instructed not to simply average the two signals

### Evaluation Framework

Three-level comparison on a balanced, reproducible sample of 60 WELFake articles:

| Level | Method | Accuracy | Avg Latency |
|---|---|---|---|
| 1 | Classical baseline (BERT, fine-tuned) | 98.33% | 0.027s |
| 2 | Single MCP call (`classify_claim` only) | 50.00% | ~4.5s |
| 3 | Full multi-agent (Content + Network + Supervisor) | 51.67% | 8.51s |

Full writeup, including why the agent underperformed the baseline here, in [`evaluation/EVALUATION_RESULTS.md`](evaluation/EVALUATION_RESULTS.md).

### Docker Compose

Two containers - `mcp-server` and `agent` - communicating over the real MCP protocol via Docker's internal network, not direct imports. `data/` (DuckDB + Chroma) is mounted as a volume into the MCP server container, not baked into the image.

### Streamlit UI

Runs as an MCP client (same `call_tool()` path used by the evaluation scripts), showing the final verdict, a breakdown of the Content and Network agents' individual reasoning, and the raw evidence retrieved from FEVER.

## Datasets & Licensing

- **WELFake** (Verma, Agrawal, Amorim & Prodan, IEEE TCSS 2021, DOI: 10.1109/TCSS.2021.3068519) - 72,134 news articles with fake/real labels. Licensed CC BY 4.0. Downloaded from Kaggle. A small balanced evaluation sample (`evaluation/eval_sample.csv`, 60 articles) is redistributed in this repo under the same license, with attribution as above; the full raw dataset is not redistributed.

- **UPFD** (Dou, Shu, Xia, Yu & Sun, "User Preference-aware Fake News Detection," SIGIR '21) - propagation graphs built on the PolitiFact/GossipCop subsets of FakeNewsNet (Shu et al., 2018). Accessed via `torch_geometric`. Not redistributed in this repo.

- **FEVER** (Thorne et al., NAACL 2018) - 185K claims verified against Wikipedia, used here as the RAG fact-check corpus. Licensed CC BY-SA 3.0 (the annotations incorporate Wikipedia content). Downloaded directly from [fever.ai](https://fever.ai/dataset/fever.html). Not redistributed in this repo - data files are gitignored.

## Project Structure

```
├── dbt_project/        # staging, intermediate, marts models
├── rag/                 # Chroma ingestion scripts (FEVER)
├── mcp_server/          # MCP server exposing the five tools above
├── agent/               # LangGraph nodes (Content, Network, Supervisor) + MCP client
├── evaluation/          # sample creation, BERT baseline, MCP-level runs, results writeup
├── prompts/             # versioned LLM prompts, one folder per agent/component
├── ingest/              # raw data loading into DuckDB
├── shared_utils.py      # Anthropic client + JSON parsing, shared by server and agent
├── app.py               # Streamlit UI
├── docker-compose.yml
└── data/                # local data + DuckDB file + Chroma store (gitignored)
```

## Setup

### Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build the dbt marts
cd dbt_project && dbt run

# Build the RAG vector store (downloads FEVER if not already present)
python3 rag/build_vector_store.py

# Start the MCP server (one terminal)
python3 mcp_server/server.py

# Run the full agent (another terminal)
python3 agent/supervisor.py

# Or launch the UI instead of the CLI
streamlit run app.py
```

Requires an `ANTHROPIC_API_KEY` in a local `.env` file (not committed).

### Docker Compose

```bash
docker compose up
```

Builds and runs both services (`mcp-server`, `agent`) with the MCP server's health checked before the agent starts. Same `.env` file requirement as above.

## Project Learnings

Notes on what building and evaluating this system actually revealed - kept here as a record of what worked, what didn't, and why.

**A RAG corpus is only as useful as its overlap with the task's claim distribution.** `classify_claim` retrieves evidence from FEVER, a corpus of general factual claims grounded in Wikipedia (e.g. "Paris is in France"). WELFake article headlines make specific, time-bound claims about real-world events, people, and politics. These two claim types rarely overlap semantically, so retrieval consistently returned irrelevant evidence, and the model correctly (per its own instructions) returned NOT ENOUGH INFO rather than guessing - both when queried with article titles and with opening-paragraph text. The result: the single MCP call and full multi-agent levels scored close to chance (50-52%) on the evaluation sample, far below a fine-tuned BERT baseline (98.33%) trained directly on WELFake's own distribution. Multi-agent orchestration cannot compensate for a retrieval corpus that doesn't cover the task domain - reasoning on top of irrelevant evidence still produces an uninformative verdict, no matter how many agents review it.

**Two independent evidence axes only add value if they can be evaluated on the same instance.** The system was designed to combine two signals - claim content and propagation pattern - precisely because they're independent (a true claim can spread through a suspicious network, and a false one can spread organically). But WELFake (article text) and UPFD (propagation graphs) share no common identifier, so the Network Agent had no `graph_id` to work with for any article in the evaluation sample, and correctly returned SKIPPED every time, by design. This didn't lower the accuracy score, but it meant the evaluation could only test the Content Agent + Supervisor path - the Network Agent's actual contribution remains unverified. A meaningful test of it would require a dataset providing both article text and propagation data for the same claims.

**The Supervisor showed a consistent misattribution pattern, not classical hallucination.** Across multiple independent runs, the Supervisor's stated reasoning treated an unrelated claim retrieved by RAG (e.g. "Haifa is home to the Eiffel Tower", retrieved for a query about the Eiffel Tower being in Paris) as if it were a related sub-claim casting doubt on the original claim - rather than recognizing it as a separate, unrelated claim that happened to be semantically similar. The model didn't invent facts; it drew an incorrect connection between two real, separately-retrieved evidence items. This is a distinct failure mode from hallucination and worth checking for explicitly in any evaluation of multi-document RAG reasoning: not just "is the final label correct," but "is the stated reasoning actually justified by the evidence provided."

**A validation score can hide the truth about generalization - and vice versa.** During BERT fine-tuning, the validation accuracy (98.75%) and the eventual evaluation-sample accuracy (98.33%) came out nearly identical, which confirmed the model was genuinely generalizing rather than overfitting to some artifact of how the training pool was sampled. That agreement was worth explicitly checking, not assuming - a validation set drawn from the same pool as the training data can look reassuring while still hiding leakage, if the pool itself has structure (e.g. per-source writing style) that doesn't reflect the deployment distribution.

**A service that works locally can still be unreachable from another container - for several independent reasons.** Moving the MCP server and agent into separate Docker containers surfaced three distinct issues that were invisible during local testing (where client and server share the same machine, so `127.0.0.1` works for both): the server was bound to `127.0.0.1` instead of `0.0.0.0`, so it only accepted connections from inside its own container; the healthcheck used a plain HTTP GET, which the MCP endpoint correctly rejected with 406 since it expects specific headers - a case where a non-200 response was actually evidence the server was alive, not down; and `pandas`, a transitive dependency of DuckDB's `.fetchdf()`, was missing from the trimmed-down Docker requirements file because it's never directly imported in the code. Each surfaced only once the two sides were actually communicating over a real network instead of a shared process - a reminder that "works locally" and "works as two networked services" are different claims that both need to be tested.

## Overview

Detecting misinformation isn't just a text classification problem - a claim's factual accuracy and the way it spreads through a network are two different, often complementary signals. This project explores whether an agentic system that reasons over both - grounding claims against a fact-check corpus via RAG, and separately analyzing propagation patterns for signs of coordinated amplification - can outperform a single-pass classifier, and where that approach's actual limits are.

The project is built as a full pipeline rather than a single script: a dbt-modeled data layer, a RAG-backed fact-checking store, an MCP server exposing that layer as tools, a multi-agent system built on LangGraph, and an evaluation framework that measures the agent's added value against classical baselines rather than assuming it.