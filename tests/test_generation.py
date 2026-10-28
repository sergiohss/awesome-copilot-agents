from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
import os
import shutil
from pathlib import Path, PurePosixPath
import unicodedata

import pytest
import yaml

from aca_tools.cli import main as cli_main
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
PACKAGE_ROOTS = {
    PurePosixPath("packages/manifests/repository.json"): (
        "repository",
        PurePosixPath("."),
    ),
    PurePosixPath("packages/manifests/repository-portable.json"): (
        "repository-portable",
        PurePosixPath("packages/repository/portable"),
    ),
    PurePosixPath("packages/manifests/user-cli.json"): (
        "user-cli",
        PurePosixPath("packages/user/cli"),
    ),
    PurePosixPath("packages/manifests/user-vscode.json"): (
        "user-vscode",
        PurePosixPath("packages/user/vscode"),
    ),
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


def _owned_set_snapshot(
    root: Path,
) -> dict[PurePosixPath, tuple[str, bytes]]:
    entries: dict[PurePosixPath, tuple[str, bytes]] = {}
    for top in (root / ".github", root / "packages"):
        if not top.exists() and not top.is_symlink():
            continue
        paths = (top, *sorted(top.rglob("*")))
        for path in paths:
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if path.is_symlink():
                entries[relative] = ("symlink", os.readlink(path).encode())
            elif path.is_file():
                entries[relative] = ("file", path.read_bytes())
            elif path.is_dir():
                entries[relative] = ("directory", b"")
    return entries


def _package_snapshots(
    root: Path,
) -> dict[str, dict[PurePosixPath, bytes]]:
    package_roots = {
        "repository": (root / ".github", PurePosixPath(".github")),
        "repository-portable": (
            root / "packages/repository/portable",
            PurePosixPath("."),
        ),
        "user-cli": (root / "packages/user/cli", PurePosixPath(".")),
        "user-vscode": (root / "packages/user/vscode", PurePosixPath(".")),
    }
    snapshots: dict[str, dict[PurePosixPath, bytes]] = {}
    for package_id, (package_root, prefix) in package_roots.items():
        files: dict[PurePosixPath, bytes] = {}
        for path in sorted(item for item in package_root.rglob("*") if item.is_file()):
            relative = PurePosixPath(path.relative_to(package_root).as_posix())
            package_path = relative if prefix == PurePosixPath(".") else prefix / relative
            files[package_path] = path.read_bytes()
        snapshots[package_id] = files
    return snapshots


def _inventory(files: dict[PurePosixPath, bytes]) -> list[dict[str, object]]:
    return [
        {
            "path": path.as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
        for path, data in sorted(files.items(), key=lambda item: item[0].as_posix())
    ]


def _make_complete_release_project(
    minimal_project,
) -> dict[str, dict[PurePosixPath, bytes]]:
    expected_fragment = b"Report evidence and never fabricate findings.\n"
    expected_instruction = b"Use repository evidence first.\n"
    assert minimal_project.fragment.read_bytes() == expected_fragment
    assert (
        minimal_project.root / "src/instructions/copilot.md"
    ).read_bytes() == expected_instruction

    expected = {
        "repository": {
            PurePosixPath(".github/copilot-instructions.md"): expected_instruction,
        },
        "repository-portable": {
            PurePosixPath(".github/copilot-instructions.md"): expected_instruction,
        },
        "user-cli": {},
        "user-vscode": {},
    }
    agents_path = minimal_project.root / "src/catalog/agents.yaml"
    agents_document = yaml.safe_load(agents_path.read_text(encoding="utf-8"))
    template = agents_document["agents"][0]
    assert template["tools"] == ["read", "search", "execute"]
    assert template["fragments"] == ["src/fragments/ins-core.md"]
    profiles = minimal_project.root / "src/profiles"
    agents = []
    for index in range(33):
        agent_id = f"release-agent-{index:02d}"
        body = f"Release profile {index}.\n".encode()
        profile = profiles / f"{agent_id}.md"
        profile.write_bytes(body)
        agent = deepcopy(template)
        agent.update(
            {
                "id": agent_id,
                "description": f"Release agent {index}.",
                "procedure_ids": [f"PROC-{index % 21:02d}"],
                "profile": f"src/profiles/{agent_id}.md",
            }
        )
        agents.append(agent)

        rendered = (
            f"---\n"
            f"name: {agent_id}\n"
            f'description: "Release agent {index}."\n'
            f"tools: [read, search, execute]\n"
            f"---\n\n"
            f"Release profile {index}.\n\n"
            f"Report evidence and never fabricate findings.\n"
        ).encode()
        filename = f"{agent_id}.agent.md"
        expected["repository"][
            PurePosixPath(".github/agents") / filename
        ] = rendered
        expected["repository-portable"][
            PurePosixPath(".github/agents") / filename
        ] = rendered
        expected["user-cli"][
            PurePosixPath(".copilot/agents") / filename
        ] = rendered
        expected["user-vscode"][PurePosixPath("agents") / filename] = rendered
    agents_path.write_text(
        yaml.safe_dump({"agents": agents}, sort_keys=False),
        encoding="utf-8",
    )

    procedures = []
    skills_root = minimal_project.root / "src/skills"
    for index in range(21):
        procedure_id = f"PROC-{index:02d}"
        skill_name = f"aca-release-skill-{index:02d}"
        procedures.append(
            {
                "id": procedure_id,
                "skill_name": skill_name,
                "contract": f"Release procedure {index}.",
            }
        )
        skill_source = f"# Release skill {index}: Cafe\u0301\r\n".encode()
        skill_data = f"# Release skill {index}: Café\n".encode()
        skill = skills_root / skill_name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_bytes(skill_source)
        expected["repository"][
            PurePosixPath(".github/skills") / skill_name / "SKILL.md"
        ] = skill_data
        expected["repository-portable"][
            PurePosixPath(".github/skills") / skill_name / "SKILL.md"
        ] = skill_data
        expected["user-cli"][
            PurePosixPath(".copilot/skills") / skill_name / "SKILL.md"
        ] = skill_data
        expected["user-vscode"][
            PurePosixPath("skills") / skill_name / "SKILL.md"
        ] = skill_data
    procedures_path = minimal_project.root / "src/catalog/procedures.yaml"
    procedures_path.write_text(
        yaml.safe_dump({"procedures": procedures}, sort_keys=False),
        encoding="utf-8",
    )
    return expected


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


def test_cli_check_forwards_flag_and_preserves_complete_owned_set(
    minimal_project,
    capsys,
):
    generate(minimal_project.root)
    minimal_project.profile.write_text("Changed canonical body.\n", encoding="utf-8")
    stale = minimal_project.root / ".github/skills/stale.txt"
    stale.write_bytes(b"stale generated content\n")
    before = _owned_set_snapshot(minimal_project.root)

    exit_code = cli_main(
        ["--check", "--root", str(minimal_project.root)],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "changed paths:" in captured.out
    assert "complete: false" in captured.out
    assert captured.err == ""
    assert _owned_set_snapshot(minimal_project.root) == before


def test_cli_release_rejects_incomplete_catalog_without_mutation(
    minimal_project,
    capsys,
):
    before = _owned_set_snapshot(minimal_project.root)

    exit_code = cli_main(
        ["--release", "--root", str(minimal_project.root)],
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "release requires exactly 33 profiles" in captured.err
    assert _owned_set_snapshot(minimal_project.root) == before


def test_cli_release_builds_complete_33_profile_21_skill_packages(
    minimal_project,
    capsys,
):
    expected_snapshots = _make_complete_release_project(minimal_project)

    exit_code = cli_main(
        ["--release", "--root", str(minimal_project.root)],
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    assert "complete: true" in captured.out
    assert captured.err == ""

    snapshots = _package_snapshots(minimal_project.root)
    assert snapshots == expected_snapshots
    assert {
        package_id: len(files)
        for package_id, files in expected_snapshots.items()
    } == {
        "repository": 55,
        "repository-portable": 55,
        "user-cli": 54,
        "user-vscode": 54,
    }

    for manifest_path, (package_id, _) in PACKAGE_ROOTS.items():
        manifest = json.loads((minimal_project.root / manifest_path).read_bytes())
        assert manifest["complete"] is True
        assert manifest["files"] == _inventory(expected_snapshots[package_id])


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
        package_id, package_root = PACKAGE_ROOTS[manifest_path]
        if package_root == PurePosixPath("."):
            package_files = {
                path: data
                for path, data in outputs.items()
                if path.parts[0] == ".github"
            }
        else:
            package_files = {
                path.relative_to(package_root): data
                for path, data in outputs.items()
                if path.is_relative_to(package_root)
            }
        expected_inventory = [
            {
                "path": path.as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
            for path, data in sorted(
                package_files.items(),
                key=lambda item: item[0].as_posix(),
            )
        ]
        manifest = json.loads(outputs[manifest_path])
        assert manifest["schema_version"] == 1
        assert manifest["package_id"] == package_id
        assert manifest["adaptation_version"] == "9.8.7"
        assert manifest["complete"] is False
        assert manifest["upstream_repository"] == "https://example.invalid/upstream.git"
        assert manifest["upstream_commit"] == "0123456789abcdef0123456789abcdef01234567"
        assert manifest["license_spdx"] == "MIT"
        assert manifest["source_attribution"] == "Copyright Example Contributors"
        assert manifest["files"] == expected_inventory
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


def test_generation_rejects_symlinked_owned_ancestor_without_external_writes(
    minimal_project,
):
    shutil.rmtree(minimal_project.root / ".github")
    external = minimal_project.root.parent / f"{minimal_project.root.name}-external"
    sentinel = external / "agents/project-analyst.agent.md"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"external sentinel\n")
    (minimal_project.root / ".github").symlink_to(external, target_is_directory=True)

    with pytest.raises(ValidationError, match=r"symbolic link.*\.github"):
        generate(minimal_project.root)

    assert sentinel.read_bytes() == b"external sentinel\n"
    assert not (minimal_project.root / "packages").exists()
    assert not tuple(minimal_project.root.glob(".aca-generate-*"))


def test_cli_rejects_symlink_root_without_mutating_target(
    minimal_project,
    capsys,
):
    lexical_root = minimal_project.root.parent / f"{minimal_project.root.name}-link"
    lexical_root.symlink_to(minimal_project.root, target_is_directory=True)
    external_sentinel = minimal_project.root.parent / (
        f"{minimal_project.root.name}-external-sentinel"
    )
    external_sentinel.write_bytes(b"outside root\n")
    target_before = _owned_set_snapshot(minimal_project.root)

    exit_code = cli_main(["--root", str(lexical_root)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "symbolic link" in captured.err
    assert _owned_set_snapshot(minimal_project.root) == target_before
    assert external_sentinel.read_bytes() == b"outside root\n"
    assert not (minimal_project.root / "packages").exists()


def test_final_owned_root_symlink_is_drift_and_replaced_without_external_writes(
    minimal_project,
):
    generate(minimal_project.root)
    expected = minimal_project.output.read_bytes()
    external = minimal_project.root.parent / f"{minimal_project.root.name}-root-link"
    external.mkdir()
    external_profile = external / minimal_project.output.name
    external_profile.write_bytes(expected)
    external_sentinel = external / "sentinel.txt"
    external_sentinel.write_bytes(b"outside root\n")
    shutil.rmtree(minimal_project.root / ".github/agents")
    (minimal_project.root / ".github/agents").symlink_to(
        external,
        target_is_directory=True,
    )

    report = generate(minimal_project.root)

    assert minimal_project.root / ".github/agents" in report.changed_paths
    assert not (minimal_project.root / ".github/agents").is_symlink()
    assert not minimal_project.output.is_symlink()
    assert minimal_project.output.read_bytes() == expected
    assert external_profile.read_bytes() == expected
    assert external_sentinel.read_bytes() == b"outside root\n"


def test_generated_leaf_symlink_is_drift_and_replaced_without_external_writes(
    minimal_project,
):
    generate(minimal_project.root)
    expected = minimal_project.output.read_bytes()
    external = minimal_project.root.parent / f"{minimal_project.root.name}-leaf-link"
    external.write_bytes(expected)
    minimal_project.output.unlink()
    minimal_project.output.symlink_to(external)

    report = generate(minimal_project.root)

    assert minimal_project.output in report.changed_paths
    assert not minimal_project.output.is_symlink()
    assert minimal_project.output.read_bytes() == expected
    assert external.read_bytes() == expected
