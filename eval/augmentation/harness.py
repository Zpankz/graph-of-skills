"""Offline augmentation harness.

Loads SkillNodes from a GoS workspace pickle, runs the three deterministic
generators with overridable config, and returns a categorised edge map so we
can score generator output without touching the live workspace.
"""
from __future__ import annotations

import gzip
import pickle
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gos.core.engine import SkillGraphRAG
from gos.core.schema import SkillEdge, SkillNode


@dataclass
class HarnessResult:
    nodes: list[SkillNode]
    edge_map: dict[tuple[str, str, str], SkillEdge]

    def edges_from(self, src: str) -> list[SkillEdge]:
        return [e for (s, _, _), e in self.edge_map.items() if s == src]

    def categorise(self) -> Counter:
        buckets: Counter = Counter()
        for e in self.edge_map.values():
            buckets[_bucket(e)] += 1
        return buckets


def _bucket(edge: SkillEdge) -> str:
    desc = edge.description or ""
    if "share tooling" in desc:
        return "primitive:tooling"
    if "share domain" in desc:
        return "primitive:domain"
    if "share allowed_tools" in desc or "share allowed tools" in desc:
        return "primitive:allowed_tools"
    if "share compatibility" in desc:
        return "primitive:compatibility"
    if "outputs feed" in desc or "inputs" in desc and "feed" in desc:
        return "primitive:io-workflow"
    if "consumes the same inputs" in desc:
        return "primitive:shared-inputs"
    if "produces the same outputs" in desc:
        return "primitive:shared-outputs"
    if "belong to" in desc and "skill family" in desc:
        return "family"
    if "explicitly references" in desc or "explicitly incorporates" in desc:
        return "name-comention"
    return f"llm:{edge.type}"


def load_nodes(workspace: str) -> list[SkillNode]:
    path = Path(workspace) / "graph_igraph_data.pklz"
    with gzip.open(path, "rb") as f:
        g = pickle.load(f)

    nodes: list[SkillNode] = []
    for v in g.vs:
        attrs: dict[str, Any] = dict(v.attributes())
        if attrs.get("type") != "Skill":
            continue
        # Drop graph-pickle-only fields before constructing SkillNode.
        attrs.pop("skill_id", None)
        attrs.pop("type", None)
        # Some scalar fields may serialize as "" — normalise.
        for k, v2 in list(attrs.items()):
            if v2 is None:
                attrs[k] = ""
        nodes.append(SkillNode(**attrs))
    return nodes


def build_engine(**overrides) -> SkillGraphRAG:
    """Construct a bare engine wired only for the primitive generators."""
    from tests.test_engine_smoke import FakeEmbeddingService, FakeLLMService

    defaults: dict[str, Any] = dict(
        llm_service=FakeLLMService(),
        embedding_service=FakeEmbeddingService(),
        working_dir="/tmp/gos-eval-harness-workdir",
        use_full_markdown=False,
        enable_semantic_linking=False,
    )
    defaults.update(overrides)
    return SkillGraphRAG(config=SkillGraphRAG.Config(**defaults))  # type: ignore[arg-type]


def run_augmentation(
    nodes: list[SkillNode],
    **overrides: Any,
) -> HarnessResult:
    engine = build_engine(**overrides)
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._primitive_overlap_edges(nodes, edge_map)
    engine._name_comention_edges(nodes, edge_map)
    engine._family_edges(nodes, edge_map)
    return HarnessResult(nodes=nodes, edge_map=edge_map)


if __name__ == "__main__":
    import sys

    ws = sys.argv[1] if len(sys.argv) > 1 else (
        "/Users/mikhail/.claude/plugins/cache/goobs/goobs/0.1.0/data/gos_workspace/obsidian_skills_v2"
    )
    nodes = load_nodes(ws)
    print(f"Loaded {len(nodes)} skills")
    result = run_augmentation(nodes)
    print(f"Generated {len(result.edge_map)} augmented edges")
    for k, v in result.categorise().most_common():
        print(f"  {v:4d}  {k}")
