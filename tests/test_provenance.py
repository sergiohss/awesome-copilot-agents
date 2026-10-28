from __future__ import annotations

import csv
from pathlib import Path

import pytest

from aca_tools.errors import ValidationError
from aca_tools.provenance import (
    SourceBaseline,
    load_baseline,
    load_lineage,
    validate_lineage_document,
    validate_partitions,
)
from aca_tools.paths import resolve_upstream_source_root


PROJECT_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = resolve_upstream_source_root(PROJECT_ROOT)


@pytest.fixture(scope="module")
def baseline() -> SourceBaseline:
    return load_baseline(PROJECT_ROOT)


def flatten(ranges):
    lines: list[int] = []
    for item in ranges:
        lines.extend(range(item.start_line, item.end_line + 1))
    return lines


def test_source_ranges_partition_every_line_once(baseline: SourceBaseline):
    agent_index = {item.path.as_posix(): item for item in baseline.agents}
    for path in sorted((PROJECT_ROOT / "provenance/lineage").glob("*.yaml")):
        lineage = load_lineage(PROJECT_ROOT, path.stem)
        source_item = agent_index[lineage.source_path.as_posix()]
        derived = [
            disposition.source_range
            for disposition in lineage.dispositions
            if disposition.kind == "source-derived"
        ]
        assert flatten(derived) == list(range(1, source_item.line_count + 1))


def test_vue_additive_behavior_has_null_range_and_authority():
    vue_lineage = load_lineage(PROJECT_ROOT, "vue-state-manager")
    additive = [item for item in vue_lineage.dispositions if item.kind == "additive"]
    assert additive
    assert {item.source_range for item in additive} == {None}
    assert {item.design_authority for item in additive} == {"VUE-03-SEMANTIC-REPAIR"}


def test_additive_status_is_rejected_on_integer_range():
    document = {
        "upstream_repository": "https://example.com/repo.git",
        "upstream_commit": "2050f3c60fcfea497f7b6b3ec6566cc316367a7e",
        "source_path": "agents/example.md",
        "source_blob_sha256": "0" * 64,
        "source_dispositions": [
            {
                "kind": "additive",
                "source_range": {"start_line": 1, "end_line": 2},
                "destination": {"type": "profile", "id": "example"},
                "semantic_status": "additive",
                "design_authority": "VUE-03-SEMANTIC-REPAIR",
            }
        ],
        "source_license_spdx": "MIT",
        "source_license_sha256": "0" * 64,
        "source_attribution": "Example",
        "adaptation_version": "0.1.0",
        "target_id": "example",
        "target_contract_id": "example-v1",
        "procedure_ids": [],
        "skill_names": [],
        "resource_destinations": [],
        "approval_record": None,
    }
    with pytest.raises(ValidationError, match="additive requires source_range: null|not valid under any"):
        validate_lineage_document(document)


def test_root_claude_approval_lineage_is_pinned(baseline: SourceBaseline):
    approval = baseline.approval_lineage
    assert approval.path.as_posix() == "CLAUDE.md"
    assert approval.sha256 == "c2cc9e33425eedfe433d0699d0085e4548897fd33a33ca1cdf51b9b67990eeed"
    assert tuple((item.start_line, item.end_line) for item in approval.ranges) == (
        (101, 106),
        (189, 189),
    )


def test_py09_unsafe_lines_are_omitted_for_safety(baseline: SourceBaseline):
    lineage = load_lineage(PROJECT_ROOT, "python-web-scraping-expert")
    unsafe = [
        item
        for item in lineage.dispositions
        if item.semantic_status == "omitted-for-safety"
    ]
    assert len(unsafe) == 1
    assert unsafe[0].source_range is not None
    assert (unsafe[0].source_range.start_line, unsafe[0].source_range.end_line) == (
        1499,
        1534,
    )


def test_agents_csv_retains_original_declared_names():
    with (PROJECT_ROOT / "provenance/agents.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    declared = {row["source_path"]: row["source_declared_name"] for row in rows}
    assert declared["agents/specialized/vue/vue-state-manager.md"] == "vue-component-architect"
    assert declared["agents/specialized/python/devops-cicd-expert.md"] == "Python DevOps/CI-CD Expert"


def test_lineage_partitions_validate_for_every_agent(baseline: SourceBaseline):
    agent_index = {item.path.as_posix(): item for item in baseline.agents}
    for path in sorted((PROJECT_ROOT / "provenance/lineage").glob("*.yaml")):
        lineage = load_lineage(PROJECT_ROOT, path.stem)
        source_item = agent_index[lineage.source_path.as_posix()]
        validate_partitions(lineage, source_item.line_count)
