# Prompts Directory

This structure separates all project prompts from the code itself, in order to:
1. Enable versioning of prompts without touching Python code
2. Document the "why" behind every change — not just the change itself
3. Show, in an interview, a real engineering workflow — not just a final result

## Folder Structure

```
prompts/
├── README.md                  <- this file
├── content_agent/
│   ├── system_prompt_v1.md
│   ├── system_prompt_v2.md
│   └── CHANGELOG.md
├── network_agent/
│   ├── system_prompt_v1.md
│   └── CHANGELOG.md
├── supervisor/
│   ├── system_prompt_v1.md
│   └── CHANGELOG.md
└── rag/
    ├── query_reformulation_v1.md
    └── CHANGELOG.md
```

## Working Rules

1. **Each prompt = a separate file**, never hardcoded inside Python code. The code loads the file (`load_prompt("supervisor/system_prompt_v2.md")`), it doesn't contain the text itself.
2. **A new version = a new file**, not an edit of the existing one. `system_prompt_v1.md` stays as-is, and `system_prompt_v2.md` is created. This way you can always compare versions or run evaluation against a previous one.
3. **Every version change is documented in the CHANGELOG.md** of that agent, following the template in `CHANGELOG_TEMPLATE.md`.
4. **In code**, always load by a config variable (e.g. `SUPERVISOR_PROMPT_VERSION = "v2"`), so it's easy to switch versions for A/B testing or rollback.

## Why this matters in interviews

It turns a question like "how did you improve your prompts?" from a vague answer into a concrete answer with numbers and an example straight from the file itself.
