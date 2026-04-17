---
name: graph-of-skills-indexing
description: Use when the user wants to build, rebuild, or extend a Graph of Skills workspace from a library of SKILL.md files. Covers initial indexing (extract metadata, embed, infer dependency/workflow/semantic edges via LLM) and incremental adds. ALWAYS invoke when the user mentions "index skills", "build skill graph", "rebuild workspace", "add skill to graph", or points at a directory of SKILL.md files and asks to make them searchable.
---

# Graph of Skills — Indexing

Use this skill to turn a directory of `SKILL.md` files into a queryable GoS workspace with embeddings and graph edges.

## Decision Tree

1. **Does a workspace already exist at the target path?**
   - No → full index (`index_skills` with `clear=true`).
   - Yes, user wants to keep existing skills → incremental add (`add_skill`).
   - Yes, user wants a fresh build → full index with `clear=true` (warn about data loss first).

2. **Does the skill library have `SKILL.md` files at the expected locations?**
   - Run `find <path> -name SKILL.md | head -n 20` to verify structure before calling `index_skills`.
   - If skills are nested weirdly, clarify with the user before proceeding.

## Preflight Checks

Before calling `mcp__graph-of-skills__index_skills`:

- Confirm `.env` has embedding + LLM API keys (at least `GEMINI_API_KEY` or `OPENAI_API_KEY`).
- Confirm `GOS_EMBEDDING_MODEL` and `GOS_EMBEDDING_DIM` match for both indexing and future retrieval.
- If the skill library is large (>200 skills), warn the user about cost and time. Rule of thumb: ~1 LLM call per skill for link inference plus 1 embedding call.
- Recommend `gemini/gemini-3.1-flash-lite-preview` for the LLM — faster and more reliable than `gemini-2.5-flash` on free-tier keys (the latter stalls for 18+ minutes on rate limits).

## Running an Index

```text
mcp__graph-of-skills__index_skills(
  path="<path to skill library>",
  workspace="<target workspace path>",
  clear=true  // or false to extend
)
```

Expected output:

- `skills_indexed` — count of SKILL.md files processed
- `edges_inferred` — count of dependency/workflow edges (excludes identity + semantic)
- `edges_total` — full edge count including identity and semantic
- `duration_s` — wall-clock time

## Incremental Add

For single-skill additions:

```text
mcp__graph-of-skills__add_skill(path="<path to SKILL.md or directory>")
```

This re-embeds only the new skill(s) and runs LLM link inference against the existing graph. Much faster than rebuilding.

## Common Failures

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "LLM service is not configured" | Missing API key | Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` |
| Hangs >5 min in linking phase | Rate-limited model | Switch `GOS_LLM_MODEL` to `gemini/gemini-3.1-flash-lite-preview` |
| Dimension mismatch at retrieval | Indexed with different embedding model | Re-index with the same model OR match `GOS_EMBEDDING_MODEL` at query time |
| "0 SKILL.md files found" | Wrong path or non-standard layout | Run `find <path> -name SKILL.md` to verify |

## Post-Index Validation

After indexing succeeds, always call `get_status` to confirm skill and edge counts match expectations. Then run one sample retrieval to validate graph quality:

```text
mcp__graph-of-skills__retrieve_skill_bundle(task="<a representative task>")
```

The result should include `SKILL_HIT` with at least one `Source:` path from the newly indexed library.
