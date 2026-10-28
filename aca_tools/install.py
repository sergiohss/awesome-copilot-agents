from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Literal

from .errors import ValidationError


InstallDisposition = Literal[
    "create", "unchanged", "replace-generated", "remove-generated", "conflict"
]

STATE_FILENAMES = {
    "repository": ".github/.awesome-copilot-agents-install.json",
    "cli": ".copilot/.awesome-copilot-agents-install.json",
    "skills-only": ".agents/.awesome-copilot-agents-install.json",
    "vscode": ".awesome-copilot-agents-install.json",
}


@dataclass(frozen=True, slots=True)
class InstallAction:
    source: Path | None
    destination: Path
    old_sha256: str | None
    new_sha256: str | None
    disposition: InstallDisposition


@dataclass(frozen=True, slots=True)
class InstallPlan:
    state_path: Path
    actions: tuple[InstallAction, ...]
    conflicts: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class InstallReport:
    applied: tuple[InstallAction, ...]
    state_path: Path


@dataclass(frozen=True, slots=True)
class UninstallPlan:
    state_path: Path
    actions: tuple[InstallAction, ...]
    mismatches: tuple[Path, ...]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _resolve_inside(root: Path, relative: PurePosixPath) -> Path:
    candidate = (root / Path(relative.as_posix())).resolve()
    root_resolved = root.resolve()
    if root_resolved not in candidate.parents and candidate != root_resolved:
        raise ValidationError(f"path escapes target root: {relative}")
    return candidate


def _load_manifest(manifest_path: Path) -> dict:
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"manifest: cannot read {manifest_path}: {error}") from error
    if not isinstance(document, dict) or "files" not in document:
        raise ValidationError("manifest: invalid package manifest")
    return document


def _load_state(state_path: Path) -> dict | None:
    if not state_path.is_file():
        return None
    try:
        document = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"install state: invalid JSON at {state_path}: {error}") from error
    return document


def plan_install(
    package_root: Path,
    target_root: Path,
    *,
    package_kind: str = "repository",
    manifest_relpath: Path | PurePosixPath = PurePosixPath("packages/manifests/repository.json"),
    portable_relpath: PurePosixPath = PurePosixPath("packages/repository/portable"),
) -> InstallPlan:
    package_root = package_root.resolve()
    target_root = target_root.resolve()
    manifest_path = _resolve_inside(package_root, PurePosixPath(str(manifest_relpath)))
    manifest = _load_manifest(manifest_path)
    portable_root = _resolve_inside(package_root, portable_relpath)
    package_id = manifest.get("package_id", "repository")
    manifest_digest = _sha256_file(manifest_path)
    state_rel = PurePosixPath(STATE_FILENAMES.get(package_kind, STATE_FILENAMES["repository"]))
    state_path = _resolve_inside(target_root, state_rel)
    prior = _load_state(state_path)
    owned: dict[str, str] = {}
    if prior is not None:
        for entry in prior.get("files", []):
            owned[entry["path"]] = entry["installed_sha256"]

    actions: list[InstallAction] = []
    conflicts: list[Path] = []
    desired_paths = {entry["path"] for entry in manifest["files"]}

    for entry in sorted(manifest["files"], key=lambda item: item["path"]):
        rel = PurePosixPath(entry["path"])
        source = _resolve_inside(portable_root, rel)
        destination = _resolve_inside(target_root, rel)
        new_digest = entry["sha256"]
        if destination.is_file():
            current = _sha256_file(destination)
            if current == new_digest:
                actions.append(
                    InstallAction(source, destination, current, new_digest, "unchanged")
                )
                continue
            if rel.as_posix() in owned and owned[rel.as_posix()] == current:
                actions.append(
                    InstallAction(source, destination, current, new_digest, "replace-generated")
                )
                continue
            conflicts.append(destination)
            actions.append(
                InstallAction(None, destination, current, new_digest, "conflict")
            )
            continue
        actions.append(InstallAction(source, destination, None, new_digest, "create"))

    if prior is not None:
        for rel_path, installed_digest in sorted(owned.items()):
            if rel_path in desired_paths:
                continue
            destination = _resolve_inside(target_root, PurePosixPath(rel_path))
            if not destination.is_file():
                continue
            current = _sha256_file(destination)
            if current != installed_digest:
                conflicts.append(destination)
                actions.append(
                    InstallAction(None, destination, current, None, "conflict")
                )
                continue
            actions.append(
                InstallAction(None, destination, current, None, "remove-generated")
            )

    return InstallPlan(state_path=state_path, actions=tuple(actions), conflicts=tuple(conflicts))


def apply_install(
    plan: InstallPlan,
    *,
    package_root: Path,
    target_root: Path,
    manifest_path: Path,
    backup_root: Path | None = None,
) -> InstallReport:
    if plan.conflicts:
        raise ValidationError(
            "install refused due to conflicts: "
            + ", ".join(str(path) for path in plan.conflicts)
        )
    target_root = target_root.resolve()
    package_root = package_root.resolve()
    manifest = _load_manifest(manifest_path)
    manifest_digest = _sha256_file(manifest_path)
    backups: list[tuple[Path, Path | None, bytes | None]] = []
    applied: list[InstallAction] = []
    try:
        for action in plan.actions:
            if action.disposition == "unchanged":
                applied.append(action)
                continue
            if action.disposition == "conflict":
                raise ValidationError(f"unexpected conflict at {action.destination}")
            if backup_root is not None and action.disposition in {
                "replace-generated",
                "remove-generated",
            }:
                backup_root.mkdir(parents=True, exist_ok=True)
                if action.destination.is_file():
                    backup_target = backup_root / action.destination.relative_to(target_root)
                    backup_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(action.destination, backup_target)
                    backups.append((action.destination, backup_target, None))
            if action.disposition == "remove-generated":
                action.destination.unlink(missing_ok=True)
                applied.append(action)
                continue
            assert action.source is not None
            action.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(action.source, action.destination)
            applied.append(action)

        state_document = {
            "schema_version": 1,
            "package_id": manifest.get("package_id", "repository"),
            "manifest_sha256": manifest_digest,
            "files": sorted(
                [
                    {
                        "path": PurePosixPath(
                            action.destination.relative_to(target_root).as_posix()
                        ).as_posix(),
                        "installed_sha256": _sha256_file(action.destination),
                    }
                    for action in plan.actions
                    if action.disposition in {"create", "replace-generated", "unchanged"}
                    and action.destination.is_file()
                ],
                key=lambda item: item["path"],
            ),
        }
        temp_state = plan.state_path.with_suffix(".tmp")
        temp_state.parent.mkdir(parents=True, exist_ok=True)
        temp_state.write_text(json.dumps(state_document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp_state.replace(plan.state_path)
    except Exception:
        for destination, backup_target, _ in reversed(backups):
            if backup_target is not None and backup_target.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_target, destination)
        raise
    return InstallReport(applied=tuple(applied), state_path=plan.state_path)


def plan_uninstall(state_path: Path, target_root: Path) -> UninstallPlan:
    target_root = target_root.resolve()
    state_path = state_path.resolve()
    prior = _load_state(state_path)
    if prior is None:
        raise ValidationError(f"install state missing: {state_path}")
    actions: list[InstallAction] = []
    mismatches: list[Path] = []
    for entry in prior.get("files", []):
        rel = PurePosixPath(entry["path"])
        destination = _resolve_inside(target_root, rel)
        if not destination.is_file():
            continue
        current = _sha256_file(destination)
        if current != entry["installed_sha256"]:
            mismatches.append(destination)
            continue
        actions.append(
            InstallAction(None, destination, current, None, "remove-generated")
        )
    return UninstallPlan(state_path=state_path, actions=tuple(actions), mismatches=tuple(mismatches))


def apply_uninstall(plan: UninstallPlan) -> None:
    if plan.mismatches:
        raise ValidationError(
            "uninstall refused due to digest mismatches: "
            + ", ".join(str(path) for path in plan.mismatches)
        )
    for action in plan.actions:
        action.destination.unlink(missing_ok=True)
    if plan.state_path.is_file():
        plan.state_path.unlink()
