---
description: Report Graph of Skills workspace status — skill count, edge count, embedding model, retrieval config
allowed-tools: mcp__graph-of-skills__get_status
---

Call `mcp__graph-of-skills__get_status` and summarize:

- workspace path
- skill count and edge count
- embedding model + dimension
- LLM model in use
- key retrieval config (seed_top_k, retrieval_top_n, max_context_chars)

If the status call fails, report the exact error verbatim and suggest the user check `.env` for missing API keys or run `/gos-bootstrap`.
