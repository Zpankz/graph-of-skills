---
name: graph-of-skills-exploration
description: Use when the user wants to browse or understand the structure of a Graph of Skills workspace — listing skills, inspecting a specific skill's metadata and graph neighbors, or auditing the library. Triggers on requests like "what skills are in the graph", "show me skills related to X", "what depends on Y", "list all skills", or "explore the skill graph".
---

# Graph of Skills — Exploration

Use this skill for read-only exploration of an existing GoS workspace. Unlike the retrieval skill (which pulls bundles for execution), this one is for browsing, auditing, and understanding graph structure.

## When To Trigger

- "List all skills in the workspace"
- "What skills are related to 3D mesh processing"
- "What does skill X depend on" / "What depends on skill X"
- "Give me the full metadata for skill Y"
- "How many skills and edges are in this workspace"
- General library audits before indexing or after expanding the graph

## Tool Selection

| Intent | Tool |
|--------|------|
| Workspace health + counts | `get_status` |
| Full list of skills | `list_skills` |
| Full metadata for one skill | `get_skill_detail` |
| Incoming/outgoing edges | `get_skill_neighbors` |
| Ranked overview for a topic | `search_skills` |

## Typical Workflows

### Full library audit

1. `get_status` — confirm workspace identity, skill/edge counts, embedding model.
2. `list_skills` — enumerate every skill by name, description, source path, domain tags.
3. (Optional) Group by domain tag or filter locally for specific topics.

### Deep dive on one skill

1. `get_skill_detail(name)` — returns I/O schema, domain tags, tooling, scripts, and all neighbors.
2. `get_skill_neighbors(name)` — if you want neighbors grouped by relation type (dependency, workflow, semantic, alternative).

### Topical exploration

1. `search_skills(query)` — quick ranked overview.
2. For each interesting hit, call `get_skill_detail` to see full metadata.
3. Follow edges with `get_skill_neighbors` to discover related skills you'd miss with pure semantic search.

## Graph Relation Types

When presenting neighbors, always group by relation type:

- **Dependency** — "skill A requires skill B to operate"
- **Workflow** — "skill A commonly runs before/after skill B"
- **Semantic** — "skill A and B are topically similar"
- **Alternative** — "skill A and B solve similar problems different ways"
- **Identity** — self-loops (usually filtered out of presentation)

## Presentation Tips

- For `list_skills` output with >50 skills, group by domain tag or first letter.
- For neighbor lists, highlight the top 3–5 edges by evidence score.
- When a skill is a graph hub (many incoming edges), call it out — these are central workflow pieces.
- When a skill is a leaf (no outgoing edges), call it out — these are terminal operations or standalone tools.

## Don'ts

- Do not retrieve skill bodies via `retrieve_skill_bundle` for pure exploration — use `get_skill_detail` instead, which is cheaper and doesn't run PPR expansion.
- Do not recommend `index_skills` from inside an exploration workflow unless the user explicitly asks to modify the graph.
