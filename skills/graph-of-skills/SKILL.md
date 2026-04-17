---
name: graph-of-skills
description: Use whenever the user's task may benefit from a specialized skill, script, or reference from a prebuilt skill library — including tasks involving niche file formats (STL, OBJ, EPUB, PPTX, DOCX), domain-specific operations (mesh analysis, PDF extraction, knowledge graph construction, Obsidian vault management, audio processing), or any situation where an existing skill likely already solves the sub-problem. Retrieves a bounded, dependency-aware bundle from the Graph of Skills graph using `retrieve_skill_bundle` as the primary MCP tool. ALWAYS invoke this skill when the user mentions processing unfamiliar file formats, asks "do we have a skill for X", works with domain-specific data, or describes a task that sounds like someone else has probably already automated it — even if they don't explicitly ask for "skills".
context: fork
agent: graph-of-skills-agent
---

# Graph of Skills — Retrieval

The Graph of Skills (GoS) ships with a prebuilt skill graph and an MCP server that Claude Code uses to retrieve relevant skills on demand. This skill tells you **when** to reach for it and **how** to use the results.

## When To Trigger

Invoke this skill whenever:

- The task involves a **niche file format** (STL, OBJ, EPUB, PPTX, DOCX with embedded data, FBX, etc.)
- The user mentions a **domain tool** that likely has an existing integration (Obsidian, FFmpeg, three.js, pandas for exotic operations, spring-boot migrations, etc.)
- The task sounds like **someone has probably automated this before** ("convert X to Y", "parse Z into W", "extract A from B")
- The user asks directly: "is there a skill for...", "what skills are available for...", "retrieve skills that..."
- You are about to write a script from scratch for a niche operation — check for an existing skill first.

Do **not** invoke this skill for:

- General programming questions with no domain specificity
- Tasks already well-covered by the current conversation's context
- Pure reasoning, planning, or code review

## Core Tool: `retrieve_skill_bundle`

This is the primary entry point. It returns full SKILL.md bodies, source paths, script entrypoints, and graph edge evidence.

**Good query patterns** (priority: `goal > artifact > operation > constraint`):

```text
update embedded xlsx in pptx and preserve formulas
parse STL mesh into connected components and compute volume
convert EPUB to atomic markdown with wikilinks for Obsidian
extract text from receipts into xlsx preserving rows
```

**Bad query patterns** (avoid):

```text
please solve this task
help with a benchmark
make everything work
<dump of entire conversation history>
```

## Workflow

1. **Construct a compact query** — short noun/verb phrase with concrete goal, artifact/format, operation, and verifier constraint.
2. **Call `mcp__graph-of-skills__retrieve_skill_bundle`** with the query.
3. **Check `Retrieval Status`:**
   - `NO_SKILL_HIT` → state this explicitly, then continue on a no-skill path.
   - `SKILL_HIT` → extract the exact `Source:` paths.
4. **Inspect task requirements** (tests, verifier, minimum acceptance) before implementing.
5. **Read referenced scripts via Source paths** — do not reconstruct or search.
6. **Follow retrieved skill instructions** — treat them as constraints on implementation, not starting suggestions.
7. **Re-query with a narrower subproblem** if the task shifts.

## Complementary Tools

| Tool | Use When |
|------|----------|
| `search_skills` | Want a ranked overview before committing to a bundle |
| `get_skill_neighbors` | Already have one skill, need to explore its dependency/workflow graph |
| `get_skill_detail` | Need full metadata (I/O schema, domain tags) for one skill |
| `hydrate_skills` | Know the exact skill name(s), want to load directly |
| `list_skills` | Auditing the full library (rare) |
| `get_status` | Workspace sanity check |

## Slash Commands

Users can also invoke these directly:

- `/gos-retrieve <task>` — the primary retrieval entry point
- `/gos-search <query>` — quick ranked overview
- `/gos-neighbors <skill-name>` — explore graph edges
- `/gos-status` — workspace health
- `/gos-bootstrap` — first-time setup
- `/gos-index <path>` — build a workspace from a skill directory
- `/gos-add <path>` — incrementally add a new skill

## Guardrails

- **Do not over-scope.** A skill retrieval is a constraint, not permission to explore.
- **Do not fabricate skill hits.** If status is `NO_SKILL_HIT`, say so.
- **Do not reconstruct Source paths.** Use exactly what retrieval returns.
- **Prefer 1–2 targeted calls** over scanning the whole library.
- **Take the shortest path to verifier pass.** Satisfy minimum requirements first.
