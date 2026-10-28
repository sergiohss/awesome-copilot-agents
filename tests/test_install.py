from __future__ import annotations

import json
from pathlib import Path

import pytest

from aca_tools.errors import ValidationError
from aca_tools.install import apply_install, apply_uninstall, plan_install, plan_uninstall


PROJECT_ROOT = Path(__file__).parents[1]
PORTABLE_ROOT = PROJECT_ROOT / "packages/repository/portable"
MANIFEST = PROJECT_ROOT / "packages/manifests/repository.json"


def test_fresh_repository_install_is_idempotent(tmp_path: Path):
    target = tmp_path / "repo with spaces"
    plan = plan_install(PROJECT_ROOT, target, manifest_relpath=Path("packages/manifests/repository.json"))
    assert not plan.conflicts
    report = apply_install(
        plan,
        package_root=PORTABLE_ROOT,
        target_root=target,
        manifest_path=MANIFEST,
    )
    assert report.state_path.is_file()
    second = plan_install(PROJECT_ROOT, target, manifest_relpath=Path("packages/manifests/repository.json"))
    assert all(action.disposition == "unchanged" for action in second.actions if action.destination.is_file())


def test_user_modified_generated_file_refuses_reinstall(tmp_path: Path):
    target = tmp_path / "repo"
    plan = plan_install(PROJECT_ROOT, target, manifest_relpath=Path("packages/manifests/repository.json"))
    apply_install(
        plan,
        package_root=PORTABLE_ROOT,
        target_root=target,
        manifest_path=MANIFEST,
    )
    agent = next(
        path
        for path in target.rglob("*.agent.md")
        if path.name == "project-analyst.agent.md"
    )
    agent.write_text(agent.read_text(encoding="utf-8") + "\n# user edit\n", encoding="utf-8")
    replan = plan_install(PROJECT_ROOT, target, manifest_relpath=Path("packages/manifests/repository.json"))
    assert replan.conflicts


def test_digest_safe_uninstall(tmp_path: Path):
    target = tmp_path / "repo"
    plan = plan_install(PROJECT_ROOT, target, manifest_relpath=Path("packages/manifests/repository.json"))
    apply_install(
        plan,
        package_root=PORTABLE_ROOT,
        target_root=target,
        manifest_path=MANIFEST,
    )
    state = target / ".github/.awesome-copilot-agents-install.json"
    uninstall = plan_uninstall(state, target)
    assert not uninstall.mismatches
    apply_uninstall(uninstall)
    assert not state.exists()
    assert not any(target.rglob("*.agent.md"))


def test_digest_mismatch_uninstall_refuses(tmp_path: Path):
    target = tmp_path / "repo"
    plan = plan_install(PROJECT_ROOT, target, manifest_relpath=Path("packages/manifests/repository.json"))
    apply_install(
        plan,
        package_root=PORTABLE_ROOT,
        target_root=target,
        manifest_path=MANIFEST,
    )
    agent = next(path for path in target.rglob("*.agent.md"))
    agent.write_text("modified", encoding="utf-8")
    state = target / ".github/.awesome-copilot-agents-install.json"
    uninstall = plan_uninstall(state, target)
    assert uninstall.mismatches
    with pytest.raises(ValidationError, match="digest mismatches"):
        apply_uninstall(uninstall)
