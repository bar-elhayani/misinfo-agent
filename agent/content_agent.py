"""
Content Agent: wraps the classify_claim MCP tool inside a LangGraph node.
This is the first, simplest agent in the multi-agent system - it only
reasons about the claim's text content, not network/propagation data.

Calls classify_claim through the real MCP protocol (HTTP), not a direct
Python import - the MCP server must be running for this to work.
"""

import sys
from pathlib import Path
from typing import TypedDict

sys.path.append(str(Path(__file__).resolve().parent))

from mcp_client import call_tool


class AgentState(TypedDict):
    claim_text: str
    content_verdict: dict | None


def content_agent_node(state: dict) -> dict:
    """
    LangGraph node: takes the claim from the state, calls classify_claim
    via MCP, and returns the state updated with the content verdict.
    """
    verdict = call_tool("classify_claim", {"claim_text": state["claim_text"]})
    return {**state, "content_verdict": verdict}


from langgraph.graph import StateGraph, END

graph_builder = StateGraph(AgentState)
graph_builder.add_node("content_agent", content_agent_node)
graph_builder.set_entry_point("content_agent")
graph_builder.add_edge("content_agent", END)

graph = graph_builder.compile()


if __name__ == "__main__":
    result = graph.invoke({"claim_text": "The Eiffel Tower is in Paris.", "content_verdict": None})
    print(result)