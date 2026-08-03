# Misinformation Detection Agent

Agentic misinformation detection system combining LLM reasoning, propagation network analysis, and RAG-based fact-checking. Built with dbt, DuckDB, LangGraph, MCP, and Docker — evaluated against classical ML baselines.

## Status

This project is under active development. Below is what's currently working, and what's planned next.

### ✅ Completed

- **Data layer (dbt + DuckDB):** staging → intermediate → marts pipeline over two independent datasets:
  - **WELFake** (72,095 articles) — text-based features (`mart_articles`): clickbait signals, length metrics, missing-value flags.
  - **UPFD** (5,778 propagation graphs, PolitiFact + GossipCop) — network features (`mart_network_summary`): spread size, amplification flags, node/edge counts.
  - Note: WELFake and UPFD are separate datasets with no shared identifier — they represent two independent evidence axes (content vs. propagation), not a joined dataset.

- **RAG (Chroma + FEVER):** 165,447 fact-checked claims embedded into a persistent Chroma vector store, enabling semantic search against a Wikipedia-grounded fact-check corpus.

- **MCP Server:** exposes four tools backed by the marts and the RAG store:
  - `get_article_features(article_id)` — WELFake article features
  - `get_network_summary(graph_id)` — UPFD propagation metrics
  - `search_fact_checks(claim_text)` — semantic search over the FEVER corpus
  - `classify_claim(claim_text)` — RAG-grounded verdict (SUPPORTS / REFUTES / NOT ENOUGH INFO) via Claude, constrained to retrieved evidence only

### 🔜 Planned

- LangGraph multi-agent system (Content Agent, Network Agent, Supervisor Agent)
- Evaluation framework: classical baseline vs. single MCP call vs. full agent
- Docker Compose for all services
- Streamlit UI

## Datasets & Licensing

- **WELFake** (Verma, Agrawal, Amorim & Prodan, IEEE TCSS 2021, DOI: 10.1109/TCSS.2021.3068519) — 72,134 news articles with fake/real labels. Downloaded from Kaggle. Not redistributed in this repo.

- **UPFD** (Dou, Shu, Xia, Yu & Sun, "User Preference-aware Fake News Detection," SIGIR '21) — propagation graphs built on the PolitiFact/GossipCop subsets of FakeNewsNet (Shu et al., 2018). Accessed via `torch_geometric`. Not redistributed in this repo.

- **FEVER** (Thorne et al., NAACL 2018) — 185K claims verified against Wikipedia, used here as the RAG fact-check corpus. Licensed CC BY-SA 3.0 (the annotations incorporate Wikipedia content). Downloaded directly from [fever.ai](https://fever.ai/dataset/fever.html). Not redistributed in this repo — data files are gitignored.

## Project Structure

├── dbt_project/       # staging, intermediate, marts models
├── rag/               # Chroma ingestion scripts (FEVER)
├── mcp_server/        # MCP server exposing the four tools above
├── prompts/           # versioned LLM prompts, one folder per agent/component
├── ingest/            # raw data loading into DuckDB
└── data/              # local data + DuckDB file + Chroma store (gitignored)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build the dbt marts
cd dbt_project && dbt run

# Build the RAG vector store (downloads FEVER if not already present)
python3 rag/build_vector_store.py

# Test the MCP tools directly
python3 mcp_server/test_tools.py
```

Requires an `ANTHROPIC_API_KEY` in a local `.env` file (not committed) for the `classify_claim` tool.