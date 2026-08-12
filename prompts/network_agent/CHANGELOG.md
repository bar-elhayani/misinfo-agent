## v1 — [11.08.2026]

**What you wrote:**
Initial system prompt instructing the LLM to assess a propagation graph's spread pattern as ORGANIC, SUSPICIOUS, or INCONCLUSIVE, based on network metrics (num_nodes, edge_count, avg_out_degree, spread_size_bucket, high_amplification_flag) from mart_network_summary.

**Why this way:**
Raw network metrics alone don't indicate whether a spread pattern is suspicious - a human (or LLM) needs to interpret them. The prompt explicitly frames the decision criterion (concentrated spread from few sources = potentially coordinated) rather than leaving it to guesswork, and requires INCONCLUSIVE when data is missing or ambiguous, to avoid overconfident guessing.

**Observed result:**
Tested with graph_id "politifact_0" (72 nodes, 71 edges, only 6 unique source nodes, avg_out_degree 11.83, high_amplification_flag=False). The model correctly identified the hub-and-spoke pattern (few sources reaching many targets) as SUSPICIOUS with medium confidence, even though the high_amplification_flag itself was False - showing the model reasoned over the raw ratios rather than relying only on the pre-computed flag. Also surfaced a formatting issue: the model initially wrapped its JSON response in markdown code fences despite explicit instructions not to, which required both a prompt strengthening (explicit "no code fences" instruction) and a code-level fallback (_parse_json_response helper) to fully resolve.