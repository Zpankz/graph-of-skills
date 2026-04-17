"""Edge-quality scoring harness.

Runs the augmentation, samples edges per category, and prints them with
skill-context metadata so we can judge each edge against the rubric:

  useful   — edge explains a real, exploitable relationship
  weak     — technically true, adds no retrieval value
  spurious — misleads the retriever (wrong type, wrong direction, false positive)
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from eval.augmentation.harness import load_nodes, run_augmentation, _bucket


def format_node_context(node, max_len: int = 90) -> str:
    desc = (node.description or node.one_line_capability or "").strip()
    return desc[:max_len].replace("\n", " ")


def sample_edges(edge_map, per_bucket: int = 6, seed: int = 42) -> dict[str, list]:
    rng = random.Random(seed)
    groups: dict[str, list] = {}
    for key, e in edge_map.items():
        b = _bucket(e)
        groups.setdefault(b, []).append((key, e))
    sampled: dict[str, list] = {}
    for b, items in groups.items():
        rng.shuffle(items)
        sampled[b] = items[:per_bucket]
    return sampled


def main():
    ws = sys.argv[1] if len(sys.argv) > 1 else (
        "/Users/mikhail/.claude/plugins/cache/goobs/goobs/0.1.0/data/gos_workspace/obsidian_skills_v2"
    )
    per_bucket = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    nodes = load_nodes(ws)
    by_name = {n.name: n for n in nodes}
    result = run_augmentation(nodes)
    sampled = sample_edges(result.edge_map, per_bucket=per_bucket)

    print(f"## Harness eval on {Path(ws).name} — {len(nodes)} skills, {len(result.edge_map)} augmented edges\n")

    for bucket in sorted(sampled):
        items = sampled[bucket]
        print(f"### {bucket} ({len(items)} sampled)\n")
        for (src, dst, etype), e in items:
            s_ctx = format_node_context(by_name[src])
            d_ctx = format_node_context(by_name[dst])
            print(f"- **{src} → {dst}** [{etype}, w={e.weight:.2f}]")
            print(f"  Evidence: {e.description}")
            print(f"  Src: {s_ctx}")
            print(f"  Dst: {d_ctx}")
            print()


if __name__ == "__main__":
    main()
