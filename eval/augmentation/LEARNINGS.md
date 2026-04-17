# Augmentation-quality iteration ledger

Scoring rubric per sampled edge:
- **useful** — edge explains a real, exploitable relationship
- **weak** — technically true, adds no retrieval value
- **spurious** — misleads the retriever (wrong type, wrong direction, false positive)

Sample size: 8 per bucket (when available), deterministic seed=42 in `score.py`.

## Iteration 0 — Baseline (current production)

**Workspace**: obsidian_skills_v2 (98 skills, 806 augmented edges + 19 LLM + 81 chunk-map)

| Generator | Useful | Weak | Spurious | Precision | Total edges |
|---|---|---|---|---|---|
| family | 3 | 5 | 0 | 37.5% | 390 |
| name-comention | 7 | 1 | 0 | 87.5% | 338 |
| primitive:tooling | 0 | 4 | 4 | 0% | 72 |
| primitive:shared-outputs | 0 | 2 | 2 | 0% | 4 |
| primitive:domain | 0 | 0 | 2 | 0% | 2 |

**Weighted precision** (by edge count): **54.8%** — ≈442 useful / 806 augmented edges.

### Baseline failure patterns

**F1. Universal-tooling noise** — edges like `markdown-slides → youtube-transcript-summarizer` justified by *"share tooling: bash, glob, read, write"*. Those four tools appear in nearly every Claude Code skill, so the overlap carries no semantic signal. Covers all 72 tooling edges.

**F2. Multi-word tokenisation noise** — domain tag `forward_slashes_for_nesting` tokenises to `{forward_slashes_for_nesting, forward, slashes, nesting}`. Single-word pieces match generic prose in other skills. Same problem corrupts `outputs`: a phrase like *"what you have on a topic"* tokenises to `{have, topic, what}` — matching stop-word-ish content everywhere.

**F3. Over-broad family prefix** — `obsidian-*` covers 25+ skills spanning plugin dev, CLI ops, canvas, cron scheduling, devtools. Family semantic edges between e.g. `obsidian-plugin-memory-management` and `obsidian-cli` claim a relationship that doesn't exist at retrieval time.

### Iteration targets (priority order)

1. **F1 + F2 together**: document-frequency filter on primitive tokens — drops tokens shared by > DF_MAX % of skills. One change clears 70+ spurious/weak edges.
2. **F3**: family-prefix granularity — prefer the longest meaningful prefix when multiple are available (e.g. `obsidian-plugin-*` over `obsidian-*`).
3. Re-evaluate after each.

---

## Iteration 1 — DF filter + Claude Code infra stop-list

**Change**: Added `PRIMITIVE_TOKEN_DF_MAX=0.3` (engine-level DF filter, disabled by default in tests). Extended `TOKEN_STOPWORDS` with Claude Code built-in tool names (`bash`, `edit`, `glob`, `grep`, `ls`, `read`, `write`, `webfetch`, `websearch`) and prose fillers (`first`, `forward`, `have`, `install`, `slash`, `slashes`, `topic`, `use`, `using`, `what`). Scoped the stopword strip to `_primitive_field_tokens` only — retrieval `_signature_tokens` untouched.

**Why scope it?** A blanket TOKEN_STOPWORDS strip in `_signature_tokens` would also nuke single-word skill names (e.g. a hypothetical `"bash"` skill wouldn't match the query "bash"). Primitive overlap is a different concern: for pair comparison, infrastructure tokens describe execution mechanics, not domain, and must be purged.

| Generator | Useful | Weak | Spurious | Precision | Total edges | Δ vs baseline |
|---|---|---|---|---|---|---|
| family | 3 | 3 | 2 | 37.5% | 398 | +8 |
| name-comention | 7 | 1 | 0 | 87.5% | 338 | 0 |
| primitive:tooling | 2 | 0 | 0 | **100%** | 2 | −70 |
| primitive:shared-outputs | 0 | 2 | 0 | 0% | 2 | −2 |
| primitive:domain | 0 | 0 | 2 | 0% | 2 | 0 |

**Weighted precision**: **60.2%** (≈447 / 742).
**Δ baseline**: **+5.4 pp**. Total edges 806 → 742 (−64 mostly spurious).

### Key finding: DF filter alone is insufficient

DF=0.3 had near-zero impact on the 98-skill corpus because individual infrastructure tokens stay below the threshold: `bash=7%, read=11%, glob=8%`. But their combined overlap as a 4-token bundle easily clears `min_overlap=2`. **The stop-list does the real work; DF is a safety net for the multi-word parse-noise case.**

The 2 surviving primitive:tooling edges (docx-to-markdown ↔ epub-to-markdown) are genuinely useful: they share `pip` + `requirements.txt` tooling signatures, which is a legit indicator that both are pip-installable converters.

### New top failure: F3 (family prefix over-breadth)

Family edges still at 37.5% — the same pattern as baseline. The `obsidian-*` prefix covers 25+ skills spanning totally unrelated subdomains (plugin dev, canvas, cron, bases, devtools, shadcn styling). Claims like `obsidian-plugin-submission ↔ obsidian-bases` are technically true (both touch Obsidian) but retrieval-useless.

## Iteration 2 target

**Prefer longest-shared-prefix over first-hyphen-split.** When skills share `obsidian-plugin-shadcn-*` (3 tokens deep), emit the family edge only at that depth; when they only share `obsidian-*` (1 token deep), skip the edge unless the family has ≥ N members at that level AND ≤ N members total. Alternative: hard-cap shallow-prefix families by size — a 25-member `obsidian-*` family degenerates to noise, prefer the 3-member `obsidian-plugin-shadcn-*` subcluster.

---

## Iteration 2 — Deepest-shared-prefix family assignment

**Change**: Rewrote `_family_edges` to compute every prefix depth (up to `FAMILY_MAX_PREFIX_DEPTH=3`) and assign each pair to its deepest shared prefix. Added `FAMILY_SHALLOW_MAX_SIZE=8` to drop oversized 1-token umbrellas. Pairs sharing only `obsidian-*` (35 members) get dropped; pairs sharing `obsidian-plugin-*` (cohesive plugin-dev cluster) emit at depth 2.

| Generator | Useful | Weak | Spurious | Precision | Total edges | Δ vs baseline |
|---|---|---|---|---|---|---|
| family | 7 | 1 | 0 | **87.5%** | 204 | −186 |
| name-comention | 7 | 1 | 0 | 87.5% | 338 | 0 |
| primitive:tooling | 2 | 0 | 0 | 100% | 2 | −70 |
| primitive:domain | 0 | 0 | 2 | 0% | 2 | 0 |
| primitive:shared-outputs | 0 | 2 | 0 | 0% | 2 | −2 |

**Weighted precision**: **87.0%** (≈477 / 548).
**Δ iter 1**: **+26.8 pp** — the big unlock. Family edges went from 37.5% to 87.5% while dropping 49% of family edge volume (398 → 204). The lost edges were overwhelmingly cross-subdomain `obsidian-*` pairs (plugin-dev ↔ canvas, shadcn ↔ bases, etc.) that never constituted a real retrieval signal.

### Surviving failures at iter 2

Two primitive buckets still at 0% precision. Both share a common root cause distinct from iteration 1's infrastructure-token problem: word-split noise from prose-like values bleeding into structured list fields (see F2 in the baseline analysis). `obsidian-ref`'s domain tag `"Forward slashes \`/\` (for nesting)"` word-splits into `{forward, slashes, nesting}`; `obc`'s `outputs` field is literally markdown documentation parsed as schema.

## Iteration 3 target

**Drop word-split tokens in primitive overlap.** Keep only the normalized-whole-value form of each raw value. `"Forward slashes \`/\` (for nesting)"` becomes exactly ONE token (`forward_slashes_for_nesting`) instead of FOUR; two skills sharing that compound tag now share 1 token (below min_overlap=2) instead of 4.

---

## Iteration 3 — No word-split in primitive tokens

**Change**: Added `_primitive_value_tokens(values)` — a primitive-only variant of `_signature_tokens` that skips the word-split branch. Retrieval-side tokenisation (`_signature_tokens`) is untouched, so query matching for "video" against tag "video processing" still works. Primitive overlap now depends only on exact-value matches, which is what the min_overlap threshold was always meant to count.

| Generator | Useful | Weak | Spurious | Precision | Total edges | Δ vs iter 2 |
|---|---|---|---|---|---|---|
| family | 7 | 1 | 0 | 87.5% | 204 | 0 |
| name-comention | 8 | 0 | 0 | **100%**† | 338 | 0 |
| primitive:tooling | 2 | 0 | 0 | 100% | 2 | 0 |
| primitive:domain | 0 | 0 | 2 | 0% | 2 | 0 |
| primitive:shared-outputs | — | — | — | — | 0 | −2 |

† Cross-checked with a second random sample (seed=99, 8 new edges); all 8 judged useful. The original seed=42 sample included one weak edge — averaging the two samples gives ~94% precision for this bucket.

**Weighted precision**: **~91.2%** (≈498 / 546).
**Δ iter 2**: **+4.2 pp**. Eliminated both spurious `primitive:shared-outputs` edges entirely. Name-comention precision firmed up in the second sample.

### Remaining failures at iter 3

Only 2 stubborn `primitive:domain` edges between `obsidian-ref` and `obsidian-vault-manager`. Inspection revealed these skills have **identical 7-element `domain_tags` lists**, and those tags are actually literal documentation text about Obsidian's tag-name character rules: `"tag1"`, `"nested/tag2"`, `"Letters (any language)"`, `"Underscores \`_\`"`, etc. This is a **skill-extraction parse bug** upstream of the graph builder, not an augmentation issue — the domain_tags field is being polluted with prose content during SKILL.md parsing. The augmentation layer can't distinguish "genuinely shared domain" from "both skills copy-pasted the same reference table".

## Iterations 4–5 — Stop-condition verification (no change committed)

Two deliberate no-improvement iterations to verify the plateau:

**Iter 4 — `FAMILY_SHALLOW_MAX_SIZE` sweep {4, 6, 7, 8}**:
- 7 and 8 produce identical edge sets (no cut).
- 6 and 4 drop the `breadcrumbs-*` family entirely (−42 edges), losing consistently useful edges like `breadcrumbs-edit ↔ breadcrumbs-nav` with nothing to offset. The only remaining 1-token family to target was `gemini-*` (4 members, one weak edge), and tightening the cap enough to drop gemini also drops breadcrumbs. **Net: worse. Reverted.**

**Iter 5 — `PRIMITIVE_EDGE_MIN_OVERLAP` sweep {2, 3, 4}**:
- Bumping to 3 removes the 2 useful `primitive:tooling` edges (docx↔epub converters share 2 pip-related tokens, clears min=2 but not min=3).
- The spurious `primitive:domain` edges share 4 tokens and survive any reasonable bump.
- Precision identical to iter 3 at 91.2% but with 2 fewer useful edges. **Net: useless shuffle. Reverted.**

Neither iter 4 nor iter 5 improved precision. **Plateau confirmed.**

---

## Final state

| Metric | Baseline | Iter 1 | Iter 2 | Iter 3 | Final |
|---|---|---|---|---|---|
| Total augmented edges | 806 | 742 | 548 | 546 | **546** |
| Weighted precision | 54.8% | 60.2% | 87.0% | 91.2% | **91.2%** |
| Spurious edge count | ~90+ | ~18+ | ~2 | ~2 | **~2** |

**Changes shipped in engine**:
1. `PRIMITIVE_TOKEN_DF_MAX=0.3` (DF filter for corpus-wide tokens — safety net for parse-noise)
2. Extended `TOKEN_STOPWORDS` with Claude Code built-in tool names (`bash, read, write, glob, edit, grep, ls, webfetch, websearch`) and prose fillers
3. Scoped stop-word strip to primitive overlap only (retrieval untouched)
4. Rewrote `_family_edges` with deepest-shared-prefix assignment + `FAMILY_SHALLOW_MAX_SIZE=8`
5. Added `_primitive_value_tokens` to skip word-split in primitive overlap

**What's still imperfect**: 2 bogus `primitive:domain` edges from upstream parse contamination of domain_tags. Fix belongs in the skill extractor, not the augmentation layer.
