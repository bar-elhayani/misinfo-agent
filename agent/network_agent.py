"""
Network Agent: wraps the assess_network_pattern MCP tool inside a
LangGraph node. Reasons about propagation/spread patterns only -
independent of the Content Agent's text-based analysis.
"""

import sys
from pathlib import Path
from typing import TypedDict

sys.path.append(str(Path(__file__).resolve().parent.parent / "mcp_server"))

from server import assess_network_pattern


class AgentState(TypedDict):
    graph_id: str
    network_verdict: dict | None


def network_agent_node(state: dict) -> dict:
    """
    LangGraph node: if a graph_id is present in the state, runs
    assess_network_pattern and adds the verdict. If no graph_id was
    provided, skips network analysis entirely.
    """
    if not state.get("graph_id"):
        return {**state, "network_verdict": {"assessment": "SKIPPED", "reasoning": "No graph_id provided."}}

    verdict = assess_network_pattern(state["graph_id"])
    return {**state, "network_verdict": verdict}


from langgraph.graph import StateGraph, END

graph_builder = StateGraph(AgentState)
graph_builder.add_node("network_agent", network_agent_node)
graph_builder.set_entry_point("network_agent")
graph_builder.add_edge("network_agent", END)

graph = graph_builder.compile()


if __name__ == "__main__":
    result = graph.invoke({"graph_id": "politifact_0", "network_verdict": None})
    print(result)