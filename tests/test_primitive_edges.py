"""Regression tests for deterministic edge generators.

These tests exercise the pure-Python primitive overlap / name co-mention /
family helpers directly without spinning up the async pipeline. They lock in
invariants that the production workspace depends on:

  * determinism (identical edge sets on repeated invocations)
  * no self-loops
  * caps respected
  * incremental pass only touches edges involving new nodes
  * short names don't generate false-positive co-mentions
"""
from __future__ import annotations

from pathlib import Path
import tempfile

from gos.core.engine import SkillGraphRAG
from gos.core.schema import SkillEdge, SkillNode


def _engine(**overrides) -> SkillGraphRAG:
    """Build a SkillGraphRAG whose generators can be called synchronously.

    The primitive helpers don't touch the async state manager, so we skip
    LLM/embedding wiring entirely and reach for them as methods on a plain
    engine instance.
    """
    tmpdir = tempfile.mkdtemp(prefix="gos-prim-test-")
    defaults = dict(
        llm_service=None,
        embedding_service=None,
        working_dir=tmpdir,
        use_full_markdown=False,
        enable_semantic_linking=False,
        # Tiny test corpora trip the document-frequency filter (every token
        # has DF=100% when N=3). Disable by default so tests exercise the
        # mechanics they were written to exercise; the DF filter has its
        # own dedicated tests.
        primitive_token_df_max=1.0,
    )
    defaults.update(overrides)
    try:
        return SkillGraphRAG(config=SkillGraphRAG.Config(**defaults))  # type: ignore[arg-type]
    except Exception:
        # If wiring rejects None services on this build, fall back to the
        # fakes used by test_engine_smoke.
        from tests.test_engine_smoke import FakeEmbeddingService, FakeLLMService

        defaults.update(
            llm_service=FakeLLMService(),
            embedding_service=FakeEmbeddingService(),
        )
        return SkillGraphRAG(config=SkillGraphRAG.Config(**defaults))  # type: ignore[arg-type]


def _node(
    name: str,
    *,
    tooling: list[str] | None = None,
    domain: list[str] | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    compatibility: list[str] | None = None,
    raw_content: str = "",
) -> SkillNode:
    return SkillNode.from_lists(
        name=name,
        description=f"test skill {name}",
        tooling=tooling or [],
        domain_tags=domain or [],
        inputs=inputs or [],
        outputs=outputs or [],
        allowed_tools=allowed_tools or [],
        compatibility=compatibility or [],
        raw_content=raw_content,
    )


# ---------------------------------------------------------------------------
# _primitive_overlap_edges
# ---------------------------------------------------------------------------


def test_primitive_overlap_emits_shared_tooling_edges() -> None:
    engine = _engine()
    nodes = [
        _node("alpha", tooling=["ffmpeg", "audio", "transcription"]),
        _node("beta", tooling=["ffmpeg", "audio", "waveform"]),
        _node("gamma", tooling=["pdf", "ocr"]),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}

    emitted = engine._primitive_overlap_edges(nodes, edge_map)

    assert emitted >= 2, "alpha↔beta should produce two directed semantic edges"
    assert ("alpha", "beta", "semantic") in edge_map
    assert ("beta", "alpha", "semantic") in edge_map
    # No edge to gamma — tooling overlap is empty.
    assert ("alpha", "gamma", "semantic") not in edge_map
    assert ("gamma", "alpha", "semantic") not in edge_map


def test_primitive_overlap_emits_io_workflow_edge() -> None:
    engine = _engine()
    nodes = [
        _node("producer", outputs=["markdown-report", "summary"]),
        _node("consumer", inputs=["markdown-report", "raw text"]),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}

    engine._primitive_overlap_edges(nodes, edge_map)

    # Directional workflow: producer outputs feed consumer inputs.
    assert ("producer", "consumer", "workflow") in edge_map
    # Reverse direction should not fire because consumer has no matching outputs.
    assert ("consumer", "producer", "workflow") not in edge_map


def test_primitive_overlap_is_deterministic() -> None:
    engine = _engine()
    nodes = [
        _node("alpha", tooling=["ffmpeg", "audio"], domain=["media"]),
        _node("beta", tooling=["ffmpeg", "audio"], domain=["media"]),
        _node("gamma", tooling=["ffmpeg"], domain=["media"]),
    ]
    runs = []
    for _ in range(3):
        edge_map: dict[tuple[str, str, str], SkillEdge] = {}
        engine._primitive_overlap_edges(nodes, edge_map)
        runs.append(sorted(edge_map))
    assert runs[0] == runs[1] == runs[2]


def test_primitive_overlap_respects_per_source_cap() -> None:
    engine = _engine(primitive_edge_max_per_source=2)
    # One hub with shared tooling to 5 peers.
    nodes = [_node(f"peer_{i}", tooling=["ffmpeg", "audio", "transcription"]) for i in range(5)]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}

    engine._primitive_overlap_edges(nodes, edge_map)

    # For each source the cap caps outgoing semantic edges at 2.
    for node in nodes:
        outgoing = [e for e in edge_map.values() if e.source == node.name and e.type == "semantic"]
        assert len(outgoing) <= 2, f"{node.name} exceeded per-source cap"


def test_primitive_overlap_no_self_loops() -> None:
    engine = _engine()
    nodes = [_node("only", tooling=["pdf"], domain=["docs"])]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._primitive_overlap_edges(nodes, edge_map)
    assert edge_map == {}


def test_primitive_overlap_incremental_only_touches_new_pairs() -> None:
    engine = _engine()
    # Existing pair (0, 1) share tooling; new node (2) shares with 0 and 1.
    nodes = [
        _node("alpha", tooling=["ffmpeg", "audio"]),
        _node("beta", tooling=["ffmpeg", "audio"]),
        _node("gamma", tooling=["ffmpeg", "audio"]),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}

    engine._primitive_overlap_edges(nodes, edge_map, target_indices={2})

    # Edges involving gamma must be present.
    assert ("gamma", "alpha", "semantic") in edge_map
    assert ("alpha", "gamma", "semantic") in edge_map
    # The pre-existing alpha↔beta pair should NOT be re-emitted.
    assert ("alpha", "beta", "semantic") not in edge_map
    assert ("beta", "alpha", "semantic") not in edge_map


# ---------------------------------------------------------------------------
# _name_comention_edges
# ---------------------------------------------------------------------------


def test_name_comention_detects_explicit_mention() -> None:
    engine = _engine()
    nodes = [
        _node("router", raw_content="Use breadcrumbs-nav to resolve routes."),
        _node("breadcrumbs-nav", raw_content="Nav helper"),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._name_comention_edges(nodes, edge_map)
    assert ("router", "breadcrumbs-nav", "workflow") in edge_map
    assert ("breadcrumbs-nav", "router", "workflow") not in edge_map


def test_name_comention_ignores_short_name_false_positives() -> None:
    engine = _engine()
    # A 3-letter skill name without a hyphen must be excluded from the
    # mention dictionary — otherwise the word "pdf" anywhere would wire
    # every skill to it.
    nodes = [
        _node("pdf", raw_content="pdf skill body"),
        _node("other", raw_content="This skill exports pdf reports."),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._name_comention_edges(nodes, edge_map)
    assert ("other", "pdf", "workflow") not in edge_map


def test_name_comention_caps_fanout() -> None:
    engine = _engine(primitive_edge_max_per_source=3)
    body = " ".join([f"peer-{i:02d}" for i in range(10)])
    nodes = [_node("hub", raw_content=body)] + [
        _node(f"peer-{i:02d}") for i in range(10)
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._name_comention_edges(nodes, edge_map)
    outgoing = [e for e in edge_map.values() if e.source == "hub" and e.type == "workflow"]
    assert len(outgoing) <= 3


# ---------------------------------------------------------------------------
# _family_edges
# ---------------------------------------------------------------------------


def test_family_edges_cluster_hyphen_prefix() -> None:
    engine = _engine()
    nodes = [
        _node("breadcrumbs-nav"),
        _node("breadcrumbs-edit"),
        _node("breadcrumbs-search"),
        _node("unrelated"),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._family_edges(nodes, edge_map)

    assert ("breadcrumbs-nav", "breadcrumbs-edit", "semantic") in edge_map
    assert ("breadcrumbs-edit", "breadcrumbs-nav", "semantic") in edge_map
    assert ("unrelated", "breadcrumbs-nav", "semantic") not in edge_map


def test_family_edges_respect_short_prefix_guard() -> None:
    engine = _engine()
    # "ob" is shorter than 4 chars → the family should be skipped entirely.
    nodes = [_node("ob-one"), _node("ob-two"), _node("ob-three")]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._family_edges(nodes, edge_map)
    assert edge_map == {}


def test_family_edges_deterministic_and_capped() -> None:
    engine = _engine(family_edge_max_per_source=2)
    nodes = [_node(f"obsidian-{letter}") for letter in "abcdef"]
    outputs: list[list[tuple[str, str, str]]] = []
    for _ in range(2):
        edge_map: dict[tuple[str, str, str], SkillEdge] = {}
        engine._family_edges(nodes, edge_map)
        outputs.append(sorted(edge_map))
    assert outputs[0] == outputs[1]

    for node in nodes:
        fanout = [e for e in outputs[0] if e[0] == node.name and e[2] == "semantic"]
        assert len(fanout) <= 2


# ---------------------------------------------------------------------------
# Document-frequency filter
# ---------------------------------------------------------------------------


def test_df_filter_drops_corpus_wide_tooling_tokens() -> None:
    """When 'bash' appears in 80% of a corpus, it should stop being a
    discriminating token — pair (alpha, beta) must not earn an edge purely
    because they happen to share that universal token.
    """
    engine = _engine(primitive_token_df_max=0.3, primitive_edge_min_overlap=1)
    # 10 nodes, 8 of them share 'bash'. Only alpha + beta ALSO share the
    # discriminating tokens 'ffmpeg' and 'audio'.
    nodes = [
        _node("alpha", tooling=["bash", "ffmpeg", "audio"]),
        _node("beta", tooling=["bash", "ffmpeg", "audio"]),
        *[_node(f"other_{i}", tooling=["bash"]) for i in range(8)],
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}

    engine._primitive_overlap_edges(nodes, edge_map)

    # bash is in 10/10 nodes → always filtered. alpha↔beta still win on
    # ffmpeg+audio (2 tokens each, DF ≤ 20%).
    assert ("alpha", "beta", "semantic") in edge_map
    # None of the bash-only peers should have emerged — their overlap signal
    # depended entirely on the dropped token.
    for i in range(8):
        assert ("alpha", f"other_{i}", "semantic") not in edge_map
        assert ("beta", f"other_{i}", "semantic") not in edge_map


def test_df_filter_disabled_when_set_to_one() -> None:
    """primitive_token_df_max=1.0 is the disable flag — universal-token pairs fire.

    Uses non-stopword tooling (`ffmpeg`, `waveform`) because infrastructure
    tokens like ``bash``/``read`` are now unconditionally stripped from the
    primitive overlap pass regardless of the DF setting.
    """
    engine = _engine(primitive_token_df_max=1.0, primitive_edge_min_overlap=1)
    nodes = [
        _node("alpha", tooling=["ffmpeg", "waveform"]),
        _node("beta", tooling=["ffmpeg", "waveform"]),
    ]
    edge_map: dict[tuple[str, str, str], SkillEdge] = {}
    engine._primitive_overlap_edges(nodes, edge_map)
    # With the filter off a universal-token overlap still emits an edge.
    assert ("alpha", "beta", "semantic") in edge_map
