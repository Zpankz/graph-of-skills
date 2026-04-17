---
description: Quick ranked search over the Graph of Skills — returns skill names, scores, and graph relations for a natural-language query
argument-hint: <query describing what you need>
allowed-tools: mcp__graph-of-skills__search_skills
---

Query: $ARGUMENTS

Call `mcp__graph-of-skills__search_skills` with the query above. Present results as a compact table:

| Skill | Score | Relation Evidence |

If the user appears to want to *use* the skills (not just browse), recommend they run `/gos-retrieve` with the same query to pull the full SKILL.md bodies. If the query is vague, suggest 2–3 tighter reformulations (concrete goal + artifact + operation + constraint).
