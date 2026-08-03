"""
MCP server exposing tools backed by the dbt marts (DuckDB) and the
FEVER-based fact-check RAG collection (Chroma).
"""

import duckdb
from mcp.server import MCPServer
from pathlib import Path
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "misinfo.duckdb")
mcp = MCPServer("misinfo-agent-tools")


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



CHROMA_PATH = str(PROJECT_ROOT / "data" / "chroma")
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_factchecks_collection = _chroma_client.get_or_create_collection(name="factchecks")


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

if __name__ == "__main__":
    mcp.run()