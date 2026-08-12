## v1 — [11.08.2026]

**What you wrote:**
Initial system prompt instructing the LLM to combine a content verdict (SUPPORTS/REFUTES/NOT ENOUGH INFO) and a network verdict (ORGANIC/SUSPICIOUS/INCONCLUSIVE/SKIPPED) into one final label (LIKELY MISINFORMATION/LIKELY LEGITIMATE/INCONCLUSIVE), explicitly warning against simply averaging the two signals since they can disagree.

**Why this way:**
Content and network signals are genuinely independent axes - a factually accurate claim can spread through a coordinated/suspicious network, and a false claim can spread organically. A naive averaging approach would lose this nuance, so the prompt explicitly instructs the model to weigh both signals with judgment rather than applying a fixed formula.

**Observed result:**
Tested end-to-end with "The Eiffel Tower is in Paris." + graph_id "politifact_0". Content Agent returned NOT ENOUGH INFO (low confidence - no direct evidence match), Network Agent returned SUSPICIOUS (medium confidence - concentrated hub-and-spoke spread). Supervisor combined these into LIKELY MISINFORMATION (medium confidence), correctly avoiding a simple average.

However, this run also surfaced an important reasoning error: the Supervisor's explanation treated an unrelated claim retrieved by RAG ("Haifa is home to the Eiffel Tower") as if it were a related sub-claim casting doubt on the original claim, when it was actually just a semantically similar but unrelated claim pulled from Chroma. This is not classical hallucination (the model didn't invent facts) - it's a misattribution between separate evidence items. Worth revisiting in the Evaluation framework: check not just whether the final label is correct, but whether the stated reasoning is actually justified by the evidence provided.