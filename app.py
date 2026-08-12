"""
Streamlit UI for the misinformation detection agent. Runs as an MCP
client - same call_tool() interface used by agent/*.py - so this UI
and the automated evaluation scripts exercise the exact same code path.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent / "agent"))

from supervisor import graph

st.set_page_config(page_title="Misinformation Detection Agent", page_icon="🔍")

st.title("🔍 Misinformation Detection Agent")
st.caption("Content analysis + network propagation analysis, combined by a Supervisor agent")

with st.form("claim_form"):
    claim_text = st.text_area(
        "Claim or article headline to check",
        placeholder="e.g. The Eiffel Tower is in Paris.",
        height=80,
    )
    graph_id = st.text_input(
        "Graph ID (optional - UPFD propagation graph, e.g. politifact_0)",
        placeholder="Leave empty to skip network analysis",
    )
    submitted = st.form_submit_button("Analyze")

if submitted and claim_text.strip():
    with st.spinner("Running Content Agent, Network Agent, and Supervisor..."):
        result = graph.invoke({
            "claim_text": claim_text,
            "graph_id": graph_id.strip() or None,
            "content_verdict": None,
            "network_verdict": None,
            "final_verdict": None,
        })

    final = result.get("final_verdict", {})
    final_label = final.get("final_label", "UNKNOWN")

    label_colors = {
        "LIKELY MISINFORMATION": "🔴",
        "LIKELY LEGITIMATE": "🟢",
        "INCONCLUSIVE": "⚪",
    }
    icon = label_colors.get(final_label, "⚪")

    st.header(f"{icon} {final_label}")
    st.write(f"**Confidence:** {final.get('confidence', 'unknown')}")
    st.write(final.get("reasoning", "No reasoning provided."))

    st.divider()

    content = result.get("content_verdict", {})
    with st.expander(f"📄 Content Agent — {content.get('verdict', 'unknown')}", expanded=True):
        st.write(f"**Confidence:** {content.get('confidence', 'unknown')}")
        st.write(content.get("reasoning", ""))

        sources = content.get("sources_used", [])
        if sources:
            st.subheader("Evidence retrieved from FEVER")
            st.table([
                {
                    "Claim": s.get("claim", ""),
                    "Label": s.get("label", ""),
                    "Wikipedia source": s.get("evidence_wiki_urls", ""),
                }
                for s in sources
            ])

    network = result.get("network_verdict", {})
    with st.expander(f"🕸️ Network Agent — {network.get('assessment', 'unknown')}", expanded=True):
        st.write(f"**Confidence:** {network.get('confidence', 'unknown')}")
        st.write(network.get("reasoning", ""))

        network_data = network.get("network_data")
        if network_data:
            st.subheader("Propagation graph metrics")
            st.json(network_data)

elif submitted:
    st.warning("Please enter a claim or headline to analyze.")