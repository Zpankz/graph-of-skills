---
description: Retrieve full agent-ready skill bundle for a task — the primary GoS retrieval tool, returns SKILL.md bodies, source paths, scripts, and graph evidence
argument-hint: <task description with goal + artifact + operation + constraint>
allowed-tools: mcp__graph-of-skills__retrieve_skill_bundle
---

Task: $ARGUMENTS

Call `mcp__graph-of-skills__retrieve_skill_bundle` with the task above. Then:

1. **Check retrieval status.** If `NO_SKILL_HIT`, say so explicitly and continue without pretending a skill was used.
2. **On `SKILL_HIT`:** inspect the returned `Source:` paths and graph evidence. Summarize for the user which skills matched and what graph edges surfaced them (dependency / workflow / semantic / alternative).
3. **Use the exact `Source:` paths returned** — do not reconstruct paths from skill names or scan the skill library.
4. **Follow the retrieved skill instructions.** Read referenced scripts via the `Source:` paths before writing new code.
5. **Do not over-expand scope.** Retrieved skills are constraints on implementation, not permission to explore more branches.

Good query patterns: `goal > artifact/format > operation/API > verifier constraint`.
Bad patterns: generic asks, full conversation history, benchmark names as filler.

If the bundle is too broad, recommend narrowing the query and re-calling with lower `--top-n`.
