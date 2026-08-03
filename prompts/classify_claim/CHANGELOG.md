# Changelog — [Agent / Component Name]

Document every prompt version change here. Goal: each entry should tell a story you can repeat in an interview.

---

## v1 — [03.08.2026]

**What you wrote:**
Initial system prompt instructing the LLM to classify a claim as SUPPORTS/REFUTES/NOT ENOUGH INFO based strictly on retrieved FEVER evidence, returning structured JSON.

**Why this way:**
Constraining the model to only use retrieved evidence (not general knowledge) is the core principle that makes this a RAG system rather than a plain LLM guess. Structured JSON output allows the result to be consumed programmatically by other agents later.

**Observed result:**
Tested with "The Eiffel Tower is located in Paris." - a true claim. Retrieved evidence included related-but-not-directly-matching claims (Paris is in France, Paris is in Europe) with no exact match linking the Eiffel Tower to Paris. The model correctly returned NOT ENOUGH INFO with low confidence rather than answering from general knowledge - validating that the "use only retrieved evidence" instruction prevents hallucination even when the model likely "knows" the answer otherwise. This highlights retrieval quality as the main bottleneck, not the LLM's reasoning.

---

## v2 — [date]

**What changed from v1:**
The concrete wording change (a short diff works well).

**Why the change:**
Which problem from v1 this was meant to solve.

**Observed result:**
Comparison to v1 if possible (quantitative metric preferred: recall went from X to Y, fewer false positives, etc.).

---

## Template for a new entry

```
## v[N] — [date]

**What changed:**


**Why:**


**Result:**

```
