---
description: Incrementally add one or more SKILL.md files to an existing Graph of Skills workspace without rebuilding
argument-hint: <path to SKILL.md or directory of skills>
allowed-tools: mcp__graph-of-skills__add_skill
---

Path: $ARGUMENTS

Call `mcp__graph-of-skills__add_skill` with the given path. Before calling:

1. Verify the path points to a valid `SKILL.md` (or directory containing them).
2. Confirm the target workspace exists — run `/gos-status` first if unsure.

After adding, report:

- skill(s) added by name
- new edges inferred (incoming + outgoing)
- updated total skill and edge counts

Incremental add re-embeds only the new skills and runs link inference against the existing graph — it's much faster than a full re-index. Use this when onboarding new skills into a production workspace.
