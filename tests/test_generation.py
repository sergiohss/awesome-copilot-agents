from __future__ import annotations

import importlib
import json
import os
from pathlib import Path, PurePosixPath
import unicodedata

import pytest
import yaml

from aca_tools.errors import ValidationError
from aca_tools.generate import GenerationReport, build_outputs, generate
from aca_tools.loaders import load_catalog
from aca_tools.render import render_profile


PROFILE_OUTPUT = PurePosixPath(".github/agents/project-analyst.agent.md")
MANIFEST_PATHS = {
    PurePosixPath("packages/manifests/repository.json"),
    PurePosixPath("packages/manifests/repository-portable.json"),
    PurePosixPath("packages/manifests/user-cli.json"),
    PurePosixPath("packages/manifests/user-vscode.json"),
}


def _rendered_profile(minimal_project, target_length: int) -> str:
    agent = load_catalog(minimal_project.root).agents[0]
    fragment = minimal_project.fragment.read_text(encoding="utf-8")
    overhead = GenerationReport.scalar_count(render_profile(agent, "", [fragment]))
    body = "x" * (target_length - overhead)
    rendered = render_profile(agent, body, [fragment])
    assert GenerationReport.scalar_count(rendered) == target_length
    minimal_project.profile.write_text(body, encoding="utf-8")
    return rendered


def _owned_file_snapshot(root: Path) -> dict[PurePosixPath, bytes]:
    files: dict[PurePosixPath, bytes] = {}
    for top in (root / ".github", root / "packages"):
        if top.exists():
            for path in sorted(item for item in top.rglob("*") if item.is_file()):
                files[PurePosixPath(path.relative_to(root).as_posix())] = path.read_bytes()
    return files


def test_render_emits_exact_portable_frontmatter(minimal_project):
    agent = load_catalog(minimal_project.root).agents[0]
    assert render_profile(agent, " Body\r\n", [" Fragment\r"]) == (
        "---\n"
        "name: project-analyst\n"
        'description: "Inspect an unfamiliar repository and report evidence."\n'
        "tools: [read, search, execute]\n"
        "---\n\n"
        "Body\n\n"
        "Fragment\n"
    )


def test_render_normalizes_nfc_and_counts_complete_profile(minimal_project):
    minimal_project.profile.write_text("Cafe\u0301 😀", encoding="utf-8")
    output = build_outputs(minimal_project.root)[PROFILE_OUTPUT]
    text = output.decode("utf-8")
    assert "Café 😀" in text
    assert unicodedata.is_normalized("NFC", text)
    assert len(text) == GenerationReport.scalar_count(text)


def test_render_rejects_surrogate_code_points(minimal_project):
    agent = load_catalog(minimal_project.root).agents[0]
    with pytest.raises(ValidationError, match="surrogate"):
        render_profile(agent, "invalid \ud800", [])


def test_unknown_tool_fails_without_changing_existing_output(minimal_project):
    existing = minimal_project.output.read_bytes()
    minimal_project.set_tools(["read", "teleport"])
    with pytest.raises(ValidationError, match="teleport"):
        generate(minimal_project.root)
    assert minimal_project.output.read_bytes() == existing


def test_missing_declared_profile_fails_without_writes(minimal_project):
    existing = minimal_project.output.read_bytes()
    minimal_project.profile.unlink()
    with pytest.raises(ValidationError, match="project-analyst.*profile"):
        generate(minimal_project.root)
    assert minimal_project.output.read_bytes() == existing


def test_profile_over_warning_limit_emits_exactly_one_warning(minimal_project):
    _rendered_profile(minimal_project, 8_001)
    with pytest.warns(UserWarning, match="project-analyst.*8,001.*8,000") as caught:
        report = generate(minimal_project.root)
    assert len(caught) == 1
    assert len(report.warnings) == 1
    assert GenerationReport.scalar_count(minimal_project.output.read_text(encoding="utf-8")) == 8_001


def test_profile_over_hard_limit_fails_before_writes(minimal_project):
    generate(minimal_project.root)
    existing = _owned_file_snapshot(minimal_project.root)
    _rendered_profile(minimal_project, 12_001)
    with pytest.raises(ValidationError, match="project-analyst.*12,001.*12,000"):
        generate(minimal_project.root)
    assert _owned_file_snapshot(minimal_project.root) == existing


def test_second_generation_is_byte_identical(minimal_project):
    first = generate(minimal_project.root)
    snapshot = {path: path.read_bytes() for path in first.written_paths}
    second = generate(minimal_project.root)
    assert second.changed_paths == ()
    assert snapshot == {path: path.read_bytes() for path in first.written_paths}


def test_check_reports_drift_without_writing(minimal_project):
    generate(minimal_project.root)
    existing = minimal_project.output.read_bytes()
    minimal_project.profile.write_text("Changed canonical body.\n", encoding="utf-8")
    report = generate(minimal_project.root, check=True)
    assert minimal_project.output in report.changed_paths
    assert minimal_project.output.read_bytes() == existing


def test_release_mode_rejects_incomplete_catalog(minimal_project):
    existing = minimal_project.output.read_bytes()
    with pytest.raises(ValidationError, match="release.*33 profiles"):
        generate(minimal_project.root, require_complete=True)
    assert minimal_project.output.read_bytes() == existing


def test_outputs_match_all_package_layouts_and_manifest_metadata(minimal_project):
    outputs = build_outputs(minimal_project.root)
    assert MANIFEST_PATHS <= set(outputs)

    repository_files = {
        path: data
        for path, data in outputs.items()
        if path.parts[0] == ".github"
    }
    for path, data in repository_files.items():
        portable = PurePosixPath("packages/repository/portable") / path
        assert outputs[portable] == data

    assert outputs[PurePosixPath("packages/user/cli/.copilot/agents/project-analyst.agent.md")] == outputs[PROFILE_OUTPUT]
    assert outputs[PurePosixPath("packages/user/vscode/agents/project-analyst.agent.md")] == outputs[PROFILE_OUTPUT]
    assert not any("copilot-instructions.md" in path.as_posix() for path in outputs if path.parts[:3] == ("packages", "user", "cli"))
    assert not any("copilot-instructions.md" in path.as_posix() for path in outputs if path.parts[:3] == ("packages", "user", "vscode"))

    for manifest_path in sorted(MANIFEST_PATHS):
        manifest = json.loads(outputs[manifest_path])
        assert manifest["schema_version"] == 1
        assert manifest["adaptation_version"] == "9.8.7"
        assert manifest["complete"] is False
        assert manifest["upstream_repository"] == "https://example.invalid/upstream.git"
        assert manifest["upstream_commit"] == "0123456789abcdef0123456789abcdef01234567"
        assert manifest["license_spdx"] == "MIT"
        assert manifest["source_attribution"] == "Copyright Example Contributors"
        assert [entry["path"] for entry in manifest["files"]] == sorted(
            entry["path"] for entry in manifest["files"]
        )
        assert outputs[manifest_path].endswith(b"\n")


def test_materialized_skill_is_copied_to_each_supported_package(minimal_project):
    skill = minimal_project.root / "src/skills/aca-inventory-first-discovery"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Discovery\r\n", encoding="utf-8")
    (skill / "references/guide.md").write_text("Cafe\u0301\r\n", encoding="utf-8")
    outputs = build_outputs(minimal_project.root)
    destinations = (
        ".github/skills/aca-inventory-first-discovery",
        "packages/repository/portable/.github/skills/aca-inventory-first-discovery",
        "packages/user/cli/.copilot/skills/aca-inventory-first-discovery",
        "packages/user/vscode/skills/aca-inventory-first-discovery",
    )
    for destination in destinations:
        assert outputs[PurePosixPath(destination) / "SKILL.md"] == b"# Discovery\n"
        assert outputs[PurePosixPath(destination) / "references/guide.md"] == "Café\n".encode()


def test_path_specific_instruction_is_rendered_only_for_repository_packages(minimal_project):
    instruction = minimal_project.root / "src/instructions/python.md"
    instruction.write_text("Use Python conventions.\r\n", encoding="utf-8")
    catalog_path = minimal_project.root / "src/catalog/instructions.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["path_specific"] = [
        {"apply_to": "**/*.py", "instruction": "src/instructions/python.md"}
    ]
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")

    outputs = build_outputs(minimal_project.root)
    relative = PurePosixPath(".github/instructions/python.instructions.md")
    expected = b'---\napplyTo: "**/*.py"\n---\n\nUse Python conventions.\n'
    assert outputs[relative] == expected
    assert outputs[PurePosixPath("packages/repository/portable") / relative] == expected
    assert not any(path.name == relative.name for path in outputs if path.parts[:3] == ("packages", "user", "cli"))
    assert not any(path.name == relative.name for path in outputs if path.parts[:3] == ("packages", "user", "vscode"))


def test_replacement_failure_restores_every_previous_owned_file(minimal_project, monkeypatch):
    generate(minimal_project.root)
    previous = _owned_file_snapshot(minimal_project.root)
    minimal_project.profile.write_text("A changed profile body.\n", encoding="utf-8")

    generate_module = importlib.import_module("aca_tools.generate")
    real_replace = os.replace
    calls = 0

    def fail_during_install(source, destination):
        nonlocal calls
        calls += 1
        if calls == 10:
            raise OSError("injected replacement failure")
        return real_replace(source, destination)

    monkeypatch.setattr(generate_module.os, "replace", fail_during_install)
    with pytest.raises(ValidationError, match="injected replacement failure"):
        generate(minimal_project.root)
    assert _owned_file_snapshot(minimal_project.root) == previous


def test_generation_never_replaces_workflows(minimal_project):
    workflow = minimal_project.root / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_bytes(b"name: existing\n")
    generate(minimal_project.root)
    assert workflow.read_bytes() == b"name: existing\n"
