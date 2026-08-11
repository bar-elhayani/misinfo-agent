"""
Supervisor Agent: runs the Content Agent and Network Agent sequentially,
then combines their findings into a single final verdict.
"""

import json
import sys
from pathlib import Path
from typing import TypedDict

sys.path.append(str(Path(__file__).resolve().parent.parent / "mcp_server"))

from server import _anthropic_client, _parse_json_response

PROJECT_ROOT = Path(__file__).resolve().parent.parent

with open(PROJECT_ROOT / "prompts" / "supervisor" / "system_prompt_v1.md") as f:
    _supervisor_system_prompt = f.read()

from content_agent import content_agent_node
from network_agent import network_agent_node


class AgentState(TypedDict):
    claim_text: str
    graph_id: str | None
    content_verdict: dict | None
    network_verdict: dict | None
    final_verdict: dict | None


def supervisor_node(state: dict) -> dict:
    """
    LangGraph node: combines the content and network verdicts already
    present in the state into a single final assessment.
    """
    user_message = (
        f"Content assessment:\n{json.dumps(state['content_verdict'], indent=2)}\n\n"
        f"Network assessment:\n{json.dumps(state['network_verdict'], indent=2)}"
    )

    response = _anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=_supervisor_system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text

    try:
        result = _parse_json_response(raw_text)
    except json.JSONDecodeError:
        result = {"error": "Model did not return valid JSON", "raw_response": raw_text}

    return {**state, "final_verdict": result}


from langgraph.graph import StateGraph, END

graph_builder = StateGraph(AgentState)
graph_builder.add_node("content_agent", content_agent_node)
graph_builder.add_node("network_agent", network_agent_node)
graph_builder.add_node("supervisor", supervisor_node)

graph_builder.set_entry_point("content_agent")
graph_builder.add_edge("content_agent", "network_agent")
graph_builder.add_edge("network_agent", "supervisor")
graph_builder.add_edge("supervisor", END)

graph = graph_builder.compile()


if __name__ == "__main__":
    result = graph.invoke({
        "claim_text": "The Eiffel Tower is in Paris.",
        "graph_id": "politifact_0",
        "content_verdict": None,
        "network_verdict": None,
        "final_verdict": None,
    })
    print(json.dumps(result, indent=2))