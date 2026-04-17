---
description: First-time setup helper — verifies dependencies, API keys, workspace, and MCP registration for Graph of Skills
allowed-tools: Bash, Read, mcp__graph-of-skills__get_status
---

Walk the user through a health check for the Graph of Skills plugin. Run each step in parallel where possible and report a consolidated status table.

## Step 1: Runtime & dependencies

- Confirm `uv --version` works.
- Check `pyproject.toml` exists at the plugin root and `graph-skills` package is installed (`uv run python -c "import gos"`).

## Step 2: Environment configuration

- Confirm `.env` exists (copy from `.env.example` if missing).
- Verify at least one embedding provider is configured (`GEMINI_API_KEY`, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY`).
- Verify `GOS_EMBEDDING_MODEL` and `GOS_EMBEDDING_DIM` are set.
- Flag if `.env.example` still has placeholder keys.

## Step 3: Workspace

- Check `GOS_WORKING_DIR` (or the `--workspace` arg in `.mcp.json`) points to a real directory.
- If the workspace is empty, recommend:
  - `./scripts/download_data.sh --workspace` for prebuilt graphs, or
  - `/gos-index <path>` to build from source.

## Step 4: MCP server

- Call `mcp__graph-of-skills__get_status`. On success, report skill/edge counts.
- On failure, dump the error and suggest remediation (missing keys, workspace path wrong, dimension mismatch).

## Step 5: Report

Produce a checklist like:

```
[✓] uv installed
[✓] graph-skills package importable
[✓] .env present, Gemini key configured
[✗] workspace empty — run: ./scripts/download_data.sh --workspace
[?] MCP status check skipped (no workspace)
```

End with the single next action the user should take.
