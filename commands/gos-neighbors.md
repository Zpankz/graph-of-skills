---
description: Explore graph neighbors of a specific skill — incoming/outgoing edges by relation type (dependency, workflow, semantic, alternative)
argument-hint: <skill-name>
allowed-tools: mcp__graph-of-skills__get_skill_neighbors, mcp__graph-of-skills__get_skill_detail
---

Skill: $ARGUMENTS

1. Call `mcp__graph-of-skills__get_skill_detail` for full metadata on the target skill (I/O schema, tooling, scripts, domain tags).
2. Call `mcp__graph-of-skills__get_skill_neighbors` to fetch the edge list.

Present neighbors grouped by relation type:

- **Dependencies** (what this skill requires)
- **Workflow** (what commonly follows or precedes)
- **Semantic** (topically related)
- **Alternatives** (skills solving similar problems)

Highlight edges with high evidence scores and surface any interesting graph patterns (e.g. the skill is a hub, a leaf, or part of a tight cluster).
