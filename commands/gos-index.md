---
description: Build a Graph of Skills workspace from a directory of SKILL.md files — extracts metadata, embeds, infers dependency/workflow edges
argument-hint: <path to skill library> [--clear] [--workspace <output path>]
allowed-tools: mcp__graph-of-skills__index_skills
---

Arguments: $ARGUMENTS

Parse the arguments to extract:

- **path** — directory containing `SKILL.md` files (required)
- **workspace** — output path for the GoS workspace (optional, defaults to `GOS_WORKING_DIR`)
- **clear** — whether to rebuild from scratch (default: true for first index, false to extend)

Before calling `mcp__graph-of-skills__index_skills`:

1. Confirm the path exists and contains `SKILL.md` files (run `ls` or `find`).
2. Warn the user if the workspace path already has data and `clear=true` would erase it.
3. Verify embedding/LLM API keys are set in `.env` — indexing will fail fast without them.

Call the tool, then report:

- number of skills processed
- number of edges inferred (dependency, workflow, semantic, identity)
- embedding model used
- total time (if available)

If indexing fails mid-flight, read the error carefully — the most common causes are rate limits (switch to `gemini-3.1-flash-lite-preview`) and embedding dimension mismatch (check `GOS_EMBEDDING_DIM`).
