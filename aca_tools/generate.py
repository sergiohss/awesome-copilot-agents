from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import tomllib
from typing import Mapping
import warnings as warning_module

from .errors import ValidationError
from .loaders import load_catalog
from .manifest import build_manifest
from .models import Catalog
from .provenance import SourceBaseline, load_baseline
from .render import normalize_text, render_profile


_WARNING_LIMIT = 8_000
_HARD_LIMIT = 12_000
_OWNED_ROOTS = (
    PurePosixPath(".github/agents"),
    PurePosixPath(".github/skills"),
    PurePosixPath(".github/instructions"),
    PurePosixPath(".github/copilot-instructions.md"),
    PurePosixPath("packages/repository/portable"),
    PurePosixPath("packages/user/cli"),
    PurePosixPath("packages/user/vscode"),
    PurePosixPath("packages/manifests"),
)
_FILE_ROOTS = {PurePosixPath(".github/copilot-instructions.md")}
_MANIFEST_PATHS = {
    "repository": PurePosixPath("packages/manifests/repository.json"),
    "repository-portable": PurePosixPath(
        "packages/manifests/repository-portable.json"
    ),
    "user-cli": PurePosixPath("packages/manifests/user-cli.json"),
    "user-vscode": PurePosixPath("packages/manifests/user-vscode.json"),
}


@dataclass(frozen=True, slots=True)
class GenerationReport:
    written_paths: tuple[Path, ...]
    changed_paths: tuple[Path, ...]
    warnings: tuple[str, ...]
    complete: bool

    @staticmethod
    def scalar_count(text: str) -> int:
        for index, character in enumerate(text):
            if 0xD800 <= ord(character) <= 0xDFFF:
                raise ValidationError(
                    f"text: surrogate code point U+{ord(character):04X} at index {index}"
                )
        return len(text)


@dataclass(frozen=True, slots=True)
class _BuildResult:
    outputs: dict[PurePosixPath, bytes]
    warnings: tuple[str, ...]


def _read_text(path: Path, *, role: str) -> str:
    if path.is_symlink():
        raise ValidationError(f"{role}: symbolic links are not allowed: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValidationError(f"{role}: cannot read UTF-8 file {path}: {error}") from error
    return normalize_text(text, source=role)


def _adaptation_version(root: Path) -> str:
    path = root / "pyproject.toml"
    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValidationError(f"pyproject.toml: cannot load project metadata: {error}") from error
    project = document.get("project")
    version = project.get("version") if isinstance(project, dict) else None
    if not isinstance(version, str) or not version:
        raise ValidationError("pyproject.toml: project.version must be a non-empty string")
    return version


def _put(
    outputs: dict[PurePosixPath, bytes],
    path: PurePosixPath,
    data: bytes,
) -> None:
    if path in outputs:
        raise ValidationError(f"generated output collision: {path.as_posix()}")
    outputs[path] = data


def _materialized_skills(
    root: Path,
    catalog: Catalog,
) -> dict[PurePosixPath, bytes]:
    procedure_skill_names = [procedure.skill_name for procedure in catalog.procedures]
    if len(set(procedure_skill_names)) != len(procedure_skill_names):
        raise ValidationError("procedure catalog contains duplicate skill names")
    cataloged = set(procedure_skill_names)
    skill_root = root / "src/skills"
    if not skill_root.exists():
        return {}
    if skill_root.is_symlink() or not skill_root.is_dir():
        raise ValidationError("src/skills: must be a directory, not a symbolic link")

    outputs: dict[PurePosixPath, bytes] = {}
    for directory in sorted(skill_root.iterdir(), key=lambda path: path.name):
        if directory.is_symlink() or not directory.is_dir():
            raise ValidationError(f"src/skills: unexpected entry {directory.name}")
        if directory.name not in cataloged:
            raise ValidationError(f"src/skills: uncataloged skill directory {directory.name}")
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file() or skill_file.is_symlink():
            raise ValidationError(f"skill {directory.name}: missing declared SKILL.md")
        for source in sorted(directory.rglob("*")):
            if source.is_symlink():
                raise ValidationError(
                    f"skill {directory.name}: symbolic links are not allowed: {source}"
                )
            if not source.is_file():
                continue
            relative = PurePosixPath(source.relative_to(directory).as_posix())
            outputs[PurePosixPath(directory.name) / relative] = _read_text(
                source,
                role=f"skill {directory.name}/{relative.as_posix()}",
            ).encode("utf-8")
    return outputs


def _validate_release_catalog(
    catalog: Catalog,
    materialized_skills: Mapping[PurePosixPath, bytes],
) -> None:
    if len(catalog.agents) != 33:
        raise ValidationError(
            f"release requires exactly 33 profiles; catalog has {len(catalog.agents)}"
        )
    procedure_ids = {procedure.id for procedure in catalog.procedures}
    required_procedures = {f"PROC-{index:02d}" for index in range(21)}
    if procedure_ids != required_procedures:
        raise ValidationError("release requires exactly PROC-00 through PROC-20")
    cataloged_skills = {procedure.skill_name for procedure in catalog.procedures}
    materialized_names = {path.parts[0] for path in materialized_skills}
    if len(cataloged_skills) != 21 or materialized_names != cataloged_skills:
        missing = sorted(cataloged_skills - materialized_names)
        detail = f"; missing {', '.join(missing)}" if missing else ""
        raise ValidationError(
            f"release requires exactly 21 materialized skills{detail}"
        )


def _instruction_output_path(source: PurePosixPath) -> PurePosixPath:
    try:
        relative = source.relative_to("src/instructions")
    except ValueError as error:
        raise ValidationError(
            f"path-specific instruction must be under src/instructions: {source}"
        ) from error
    if relative.suffix != ".md":
        raise ValidationError(f"path-specific instruction must be Markdown: {source}")
    if relative.name.endswith(".instructions.md"):
        output_name = relative.name
    else:
        output_name = f"{relative.stem}.instructions.md"
    return PurePosixPath(".github/instructions") / relative.parent / output_name


def _build(root: Path, *, require_complete: bool) -> _BuildResult:
    catalog = load_catalog(root)
    baseline: SourceBaseline = load_baseline(root)
    adaptation_version = _adaptation_version(root)
    materialized_skills = _materialized_skills(root, catalog)
    if require_complete:
        _validate_release_catalog(catalog, materialized_skills)

    repository: dict[PurePosixPath, bytes] = {}
    messages: list[str] = []
    for agent in sorted(catalog.agents, key=lambda item: item.id):
        profile_path = root / agent.profile
        body = _read_text(profile_path, role=f"agent {agent.id} profile")
        fragments = [
            _read_text(root / fragment, role=f"agent {agent.id} fragment {fragment}")
            for fragment in agent.fragments
        ]
        rendered = render_profile(agent, body, fragments)
        scalar_count = GenerationReport.scalar_count(rendered)
        if scalar_count > _HARD_LIMIT:
            raise ValidationError(
                f"profile {agent.id} has {scalar_count:,} Unicode scalar values; "
                f"hard limit is {_HARD_LIMIT:,}"
            )
        if scalar_count > _WARNING_LIMIT:
            messages.append(
                f"profile {agent.id} has {scalar_count:,} Unicode scalar values; "
                f"warning limit is {_WARNING_LIMIT:,}"
            )
        _put(
            repository,
            PurePosixPath(f".github/agents/{agent.id}.agent.md"),
            rendered.encode("utf-8"),
        )

    repository_instruction = _read_text(
        root / catalog.instructions.repository,
        role="repository instruction",
    ).encode("utf-8")
    _put(
        repository,
        PurePosixPath(".github/copilot-instructions.md"),
        repository_instruction,
    )

    for entry in catalog.instructions.path_specific:
        source = PurePosixPath(str(entry["instruction"]))
        body = _read_text(
            root / source,
            role=f"path-specific instruction {source.as_posix()}",
        ).strip()
        rendered = normalize_text(
            f"---\napplyTo: {json.dumps(entry['apply_to'], ensure_ascii=False)}\n"
            f"---\n\n{body}\n",
            source=f"path-specific instruction {source.as_posix()}",
        ).encode("utf-8")
        _put(repository, _instruction_output_path(source), rendered)

    for skill_path, data in sorted(materialized_skills.items()):
        _put(repository, PurePosixPath(".github/skills") / skill_path, data)

    portable = dict(repository)
    cli: dict[PurePosixPath, bytes] = {}
    vscode: dict[PurePosixPath, bytes] = {}
    for path, data in sorted(repository.items()):
        if path.parts[:2] == (".github", "agents"):
            relative = PurePosixPath(*path.parts[2:])
            cli[PurePosixPath(".copilot/agents") / relative] = data
            vscode[PurePosixPath("agents") / relative] = data
        elif path.parts[:2] == (".github", "skills"):
            relative = PurePosixPath(*path.parts[2:])
            cli[PurePosixPath(".copilot/skills") / relative] = data
            vscode[PurePosixPath("skills") / relative] = data

    outputs: dict[PurePosixPath, bytes] = dict(repository)
    for path, data in sorted(portable.items()):
        _put(outputs, PurePosixPath("packages/repository/portable") / path, data)
    for path, data in sorted(cli.items()):
        _put(outputs, PurePosixPath("packages/user/cli") / path, data)
    for path, data in sorted(vscode.items()):
        _put(outputs, PurePosixPath("packages/user/vscode") / path, data)

    packages = {
        "repository": repository,
        "repository-portable": portable,
        "user-cli": cli,
        "user-vscode": vscode,
    }
    for package_id, files in packages.items():
        _put(
            outputs,
            _MANIFEST_PATHS[package_id],
            build_manifest(
                package_id,
                files,
                baseline=baseline,
                adaptation_version=adaptation_version,
                complete=require_complete,
            ),
        )
    return _BuildResult(
        outputs=dict(sorted(outputs.items(), key=lambda item: item[0].as_posix())),
        warnings=tuple(messages),
    )


def _emit_warnings(messages: tuple[str, ...]) -> None:
    for message in messages:
        warning_module.warn(message, UserWarning, stacklevel=3)


def build_outputs(
    root: Path,
    *,
    require_complete: bool = False,
) -> dict[PurePosixPath, bytes]:
    """Validate canonical inputs and return every deterministic output byte string."""
    result = _build(root, require_complete=require_complete)
    _emit_warnings(result.warnings)
    return result.outputs


def _validate_owned_ancestors(root: Path) -> None:
    if root.is_symlink():
        raise ValidationError(f"owned target ancestor is a symbolic link: {root}")
    checked: set[Path] = set()
    for relative in _OWNED_ROOTS:
        ancestor = root
        for part in relative.parts[:-1]:
            ancestor /= part
            if ancestor in checked:
                continue
            checked.add(ancestor)
            if ancestor.is_symlink():
                display = ancestor.relative_to(root).as_posix()
                raise ValidationError(
                    f"owned target ancestor is a symbolic link: {display}"
                )


def _existing_owned_files(root: Path) -> set[PurePosixPath]:
    files: set[PurePosixPath] = set()
    for relative in _OWNED_ROOTS:
        target = root / relative
        if target.is_symlink() or target.is_file():
            files.add(relative)
        elif target.is_dir():
            for path in target.rglob("*"):
                if path.is_symlink() or path.is_file():
                    files.add(PurePosixPath(path.relative_to(root).as_posix()))
    return files


def _path_has_symlink(root: Path, relative: PurePosixPath) -> bool:
    path = root
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            return True
    return False


def _changed_paths(
    root: Path,
    outputs: Mapping[PurePosixPath, bytes],
) -> tuple[Path, ...]:
    existing = _existing_owned_files(root)
    changed: list[Path] = []
    for relative in sorted(existing | set(outputs), key=PurePosixPath.as_posix):
        path = root / relative
        if _path_has_symlink(root, relative):
            changed.append(path)
            continue
        expected = outputs.get(relative)
        if expected is None:
            changed.append(path)
            continue
        try:
            current = path.read_bytes()
        except OSError:
            changed.append(path)
        else:
            if current != expected:
                changed.append(path)
    return tuple(changed)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _validate_stage(
    stage: Path,
    outputs: Mapping[PurePosixPath, bytes],
) -> None:
    staged_files = {
        PurePosixPath(path.relative_to(stage).as_posix())
        for path in stage.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if staged_files != set(outputs):
        raise ValidationError("staged output inventory does not match the complete build")
    for relative, expected in outputs.items():
        path = stage / relative
        if path.is_symlink() or path.read_bytes() != expected:
            raise ValidationError(f"staged output failed validation: {relative}")


def _replace_transactionally(
    root: Path,
    outputs: Mapping[PurePosixPath, bytes],
) -> None:
    temporary = Path(tempfile.mkdtemp(prefix=".aca-generate-", dir=root))
    stage = temporary / "stage"
    backup = temporary / "backup"
    backed_up: list[PurePosixPath] = []
    installed: list[PurePosixPath] = []
    try:
        for relative in _OWNED_ROOTS:
            staged_root = stage / relative
            if relative in _FILE_ROOTS:
                staged_root.parent.mkdir(parents=True, exist_ok=True)
            else:
                staged_root.mkdir(parents=True, exist_ok=True)
        for relative, data in outputs.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        _validate_stage(stage, outputs)

        for relative in _OWNED_ROOTS:
            target = root / relative
            if target.exists() or target.is_symlink():
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, saved)
                backed_up.append(relative)
        for relative in _OWNED_ROOTS:
            staged_root = stage / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_root, target)
            installed.append(relative)
    except Exception as error:
        rollback_errors: list[str] = []
        for relative in reversed(installed):
            try:
                _remove_path(root / relative)
            except OSError as rollback_error:
                rollback_errors.append(f"remove {relative}: {rollback_error}")
        for relative in reversed(backed_up):
            saved = backup / relative
            target = root / relative
            try:
                if target.exists() or target.is_symlink():
                    _remove_path(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(saved, target)
            except OSError as rollback_error:
                rollback_errors.append(f"restore {relative}: {rollback_error}")
        detail = f"; rollback errors: {'; '.join(rollback_errors)}" if rollback_errors else ""
        raise ValidationError(f"transactional replacement failed: {error}{detail}") from error
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def generate(
    root: Path,
    *,
    check: bool = False,
    require_complete: bool = False,
) -> GenerationReport:
    """Build and atomically replace every owned output root, or report drift."""
    _validate_owned_ancestors(root)
    result = _build(root, require_complete=require_complete)
    _emit_warnings(result.warnings)
    changed_paths = _changed_paths(root, result.outputs)
    if changed_paths and not check:
        _replace_transactionally(root, result.outputs)
    written_paths = tuple(root / path for path in result.outputs)
    return GenerationReport(
        written_paths=written_paths,
        changed_paths=changed_paths,
        warnings=result.warnings,
        complete=require_complete,
    )
