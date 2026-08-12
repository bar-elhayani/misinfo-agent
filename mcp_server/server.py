"""
MCP server exposing tools backed by the dbt marts (DuckDB) and the
FEVER-based fact-check RAG collection (Chroma).
"""

import json
import sys
from pathlib import Path

import chromadb
import duckdb
from mcp.server import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from shared_utils import anthropic_client, parse_json_response

DB_PATH = str(PROJECT_ROOT / "data" / "misinfo.duckdb")
CHROMA_PATH = str(PROJECT_ROOT / "data" / "chroma")

mcp = MCPServer("misinfo-agent-tools")

with open(PROJECT_ROOT / "prompts" / "classify_claim" / "system_prompt_v1.md") as f:
    _classify_claim_system_prompt = f.read()

_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_factchecks_collection = _chroma_client.get_or_create_collection(name="factchecks")

with open(PROJECT_ROOT / "prompts" / "network_agent" / "system_prompt_v1.md") as f:
    _network_agent_system_prompt = f.read()


@mcp.tool()
def get_article_features(article_id: int) -> dict:
    """
    Retrieve engineered text features for a single WELFake article
    (title, body text, clickbait signals, label, and related metrics)
    from the mart_articles dbt mart.
    """
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        result = con.execute(
            "SELECT * FROM mart_articles WHERE article_id = ?",
            [article_id],
        ).fetchdf()
    finally:
        con.close()

    if result.empty:
        return {"error": f"No article found with article_id={article_id}"}

    return result.iloc[0].to_dict()


@mcp.tool()
def get_network_summary(graph_id: str) -> dict:
    """
    Retrieve propagation network metrics for a single UPFD graph
    (spread size, amplification flag, node/edge counts, and related
    metrics) from the mart_network_summary dbt mart.
    """
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        result = con.execute(
            "SELECT * FROM mart_network_summary WHERE graph_id = ?",
            [graph_id],
        ).fetchdf()
    finally:
        con.close()

    if result.empty:
        return {"error": f"No graph found with graph_id={graph_id}"}

    return result.iloc[0].to_dict()


@mcp.tool()
def search_fact_checks(claim_text: str, n_results: int = 5) -> list[dict]:
    """
    Search the FEVER fact-check corpus for claims semantically similar
    to the given claim. Returns matching claims with their verdict
    (SUPPORTS/REFUTES/NOT ENOUGH INFO) and supporting Wikipedia sources.
    """
    results = _factchecks_collection.query(
        query_texts=[claim_text],
        n_results=n_results,
    )

    matches = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        matches.append({
            "claim": doc,
            "label": meta["label"],
            "evidence_wiki_urls": meta["evidence_wiki_urls"],
        })

    return matches

@mcp.tool()
def classify_claim(claim_text: str) -> dict:
    """
    Classify a claim as SUPPORTS, REFUTES, or NOT ENOUGH INFO by
    retrieving related evidence from the FEVER fact-check corpus
    and asking an LLM to reason over it.
    """
    evidence = search_fact_checks(claim_text, n_results=5)

    user_message = (
        f"Claim to verify: {claim_text}\n\n"
        f"Retrieved evidence:\n{json.dumps(evidence, indent=2)}"
    )

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=_classify_claim_system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text

    try:
        result = parse_json_response(raw_text)
    except json.JSONDecodeError:
        return {"error": "Model did not return valid JSON", "raw_response": raw_text}

    result["sources_used"] = evidence
    return result

@mcp.tool()
def assess_network_pattern(graph_id: str) -> dict:
    """
    Assess whether a propagation graph's spread pattern looks organic
    or suspicious/coordinated, using an LLM to reason over the network
    metrics from mart_network_summary.
    """
    network_data = get_network_summary(graph_id)

    if "error" in network_data:
        return network_data

    user_message = f"Propagation metrics:\n{json.dumps(network_data, indent=2)}"

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=_network_agent_system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text

    try:
        result = parse_json_response(raw_text)
    except json.JSONDecodeError:
        return {"error": "Model did not return valid JSON", "raw_response": raw_text}

    result["network_data"] = network_data
    return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http")