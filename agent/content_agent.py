"""
Content Agent: wraps the classify_claim MCP tool inside a LangGraph node.
This is the first, simplest agent in the multi-agent system - it only
reasons about the claim's text content, not network/propagation data.
"""

import sys
from pathlib import Path
from typing import TypedDict

# Add mcp_server/ to the import path so we can reuse classify_claim directly,
# without going through the full MCP protocol for now.
sys.path.append(str(Path(__file__).resolve().parent.parent / "mcp_server"))

from server import classify_claim


class AgentState(TypedDict):
    claim_text: str
    content_verdict: dict | None


def content_agent_node(state: AgentState) -> AgentState:
    """
    LangGraph node: takes the claim from the state, runs classify_claim,
    and returns an updated state with the verdict added.
    """
    verdict = classify_claim(state["claim_text"])
    return {"claim_text": state["claim_text"], "content_verdict": verdict}

from langgraph.graph import StateGraph, END

graph_builder = StateGraph(AgentState)
graph_builder.add_node("content_agent", content_agent_node)
graph_builder.set_entry_point("content_agent")
graph_builder.add_edge("content_agent", END)

graph = graph_builder.compile()


if __name__ == "__main__":
    result = graph.invoke({"claim_text": "The Eiffel Tower is in Paris.", "content_verdict": None})
    print(result)