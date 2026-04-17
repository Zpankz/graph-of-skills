from pathlib import Path

from gos.experiments import get_experiment_preset, resolve_preset_documents


def test_research_subset_preset_resolves_expected_skill_documents():
    preset = get_experiment_preset("research-subset")

    documents = resolve_preset_documents(
        preset,
        base_dir=Path(__file__).resolve().parent.parent,
    )

    assert len(documents) == 5
    parsed_names = {parsed.name for _, _, _, parsed in documents}
    assert "graph-of-skills" in parsed_names
    assert "graph-of-skills-exploration" in parsed_names
    assert "vector-skills-retriever" in parsed_names
