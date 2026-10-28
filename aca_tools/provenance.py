from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any

from jsonschema import Draft202012Validator

from .errors import ValidationError


@dataclass(frozen=True, slots=True)
class SourceFileBaseline:
    path: PurePosixPath
    line_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SourceRange:
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class LicenseBaseline:
    path: PurePosixPath
    spdx: str
    sha256: str
    attribution: str


@dataclass(frozen=True, slots=True)
class ApprovalBaseline:
    path: PurePosixPath
    sha256: str
    ranges: tuple[SourceRange, ...]


@dataclass(frozen=True, slots=True)
class SourceBaseline:
    schema_version: int
    adaptation_version: str
    upstream_repository: str
    upstream_commit: str
    agents: tuple[SourceFileBaseline, ...]
    license: LicenseBaseline
    approval: ApprovalBaseline

    @property
    def approval_lineage(self) -> ApprovalBaseline:
        return self.approval


@dataclass(frozen=True, slots=True)
class LineageDestination:
    type: str
    id: str


@dataclass(frozen=True, slots=True)
class LineageDisposition:
    kind: str
    source_range: SourceRange | None
    destination: LineageDestination
    semantic_status: str
    design_authority: str | None = None


@dataclass(frozen=True, slots=True)
class Lineage:
    upstream_repository: str
    upstream_commit: str
    source_path: PurePosixPath
    source_blob_sha256: str
    dispositions: tuple[LineageDisposition, ...]
    source_license_spdx: str
    source_license_sha256: str
    source_attribution: str
    adaptation_version: str
    target_id: str
    target_contract_id: str
    procedure_ids: tuple[str, ...]
    skill_names: tuple[str, ...]
    resource_destinations: tuple[str, ...]
    approval_record: str | None


@dataclass(frozen=True, slots=True)
class VerificationReport:
    matched_agents: int
    expected_agents: int
    license_matches: bool
    approval_matches: bool
    mismatches: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return (
            self.matched_agents == self.expected_agents
            and self.license_matches
            and self.approval_matches
            and not self.mismatches
        )


def _field_path(parts: list[object]) -> str:
    result = ""
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += ("." if result else "") + str(part)
    return result or "baseline"


def _strict_posix_path(value: str, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ValidationError(f"{field}: must be a normalized POSIX relative path")
    return path


def _load_strict_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValidationError(f"{path.name}: cannot read UTF-8 JSON: {error}") from error

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"{path.name}: duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        document = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except ValidationError:
        raise
    except json.JSONDecodeError as error:
        raise ValidationError(f"{path.name}: invalid JSON: {error}") from error
    if not isinstance(document, dict):
        raise ValidationError(f"{path.name}: document must be an object")
    return document


def load_baseline(root: Path) -> SourceBaseline:
    baseline_path = root / "provenance/source-baseline.json"
    schema_path = root / "src/schemas/source-baseline.schema.json"
    document = _load_strict_json(baseline_path)
    schema = _load_strict_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        raise ValidationError(f"{_field_path(list(error.absolute_path))}: {error.message}")

    agents: list[SourceFileBaseline] = []
    seen_paths: set[PurePosixPath] = set()
    for index, item in enumerate(document["agents"]):
        path = _strict_posix_path(item["path"], f"agents[{index}].path")
        if path in seen_paths:
            raise ValidationError(f"duplicate source path: {path}")
        seen_paths.add(path)
        agents.append(
            SourceFileBaseline(path=path, line_count=item["line_count"], sha256=item["sha256"])
        )

    approval_ranges = tuple(SourceRange(**item) for item in document["approval"]["ranges"])
    previous_end = 0
    for index, source_range in enumerate(approval_ranges):
        if source_range.start_line > source_range.end_line:
            raise ValidationError(f"approval.ranges[{index}]: start_line exceeds end_line")
        if source_range.start_line <= previous_end:
            raise ValidationError(f"approval.ranges[{index}]: ranges overlap or are unordered")
        previous_end = source_range.end_line

    return SourceBaseline(
        schema_version=document["schema_version"],
        adaptation_version=document["adaptation_version"],
        upstream_repository=document["upstream_repository"],
        upstream_commit=document["upstream_commit"],
        agents=tuple(agents),
        license=LicenseBaseline(
            path=_strict_posix_path(document["license"]["path"], "license.path"),
            spdx=document["license"]["spdx"],
            sha256=document["license"]["sha256"],
            attribution=document["license"]["attribution"],
        ),
        approval=ApprovalBaseline(
            path=_strict_posix_path(document["approval"]["path"], "approval.path"),
            sha256=document["approval"]["sha256"],
            ranges=approval_ranges,
        ),
    )


def _pinned_blob(source_root: Path, commit: str, path: PurePosixPath) -> bytes | None:
    try:
        return subprocess.run(
            ["git", "show", f"{commit}:{path.as_posix()}"],
            cwd=source_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verify_file(
    source_root: Path,
    commit: str,
    item: SourceFileBaseline,
    *,
    check_line_count: bool,
) -> tuple[bool, list[str]]:
    path_text = item.path.as_posix()
    pinned = _pinned_blob(source_root, commit, item.path)
    if pinned is None:
        return False, [f"{path_text}: pinned blob unavailable at {commit}"]
    issues: list[str] = []
    if _sha256(pinned) != item.sha256:
        issues.append(f"{path_text}: baseline SHA-256 does not match pinned blob")
    if check_line_count and len(pinned.decode("utf-8").splitlines()) != item.line_count:
        issues.append(f"{path_text}: baseline line count does not match pinned blob")
    current_path = source_root / item.path
    try:
        current = current_path.read_bytes()
    except OSError:
        issues.append(f"{path_text}: current source file is missing")
    else:
        if current != pinned:
            issues.append(f"{path_text}: current bytes do not match pinned blob")
    return not issues, issues


def verify_upstream(source_root: Path, baseline: SourceBaseline) -> VerificationReport:
    """Compare pinned and current upstream bytes against the immutable baseline."""
    mismatches: list[str] = []
    matched_agents = 0
    for item in baseline.agents:
        matches, issues = _verify_file(
            source_root,
            baseline.upstream_commit,
            item,
            check_line_count=True,
        )
        if matches:
            matched_agents += 1
        mismatches.extend(issues)

    license_item = SourceFileBaseline(
        path=baseline.license.path,
        line_count=0,
        sha256=baseline.license.sha256,
    )
    license_matches, license_issues = _verify_file(
        source_root,
        baseline.upstream_commit,
        license_item,
        check_line_count=False,
    )
    mismatches.extend(license_issues)

    approval_item = SourceFileBaseline(
        path=baseline.approval.path,
        line_count=0,
        sha256=baseline.approval.sha256,
    )
    approval_matches, approval_issues = _verify_file(
        source_root,
        baseline.upstream_commit,
        approval_item,
        check_line_count=False,
    )
    if approval_matches:
        approval_blob = _pinned_blob(
            source_root, baseline.upstream_commit, baseline.approval.path
        )
        assert approval_blob is not None
        line_count = len(approval_blob.decode("utf-8").splitlines())
        if any(source_range.end_line > line_count for source_range in baseline.approval.ranges):
            approval_matches = False
            approval_issues.append(
                f"{baseline.approval.path.as_posix()}: approval range exceeds pinned file"
            )
    mismatches.extend(approval_issues)

    return VerificationReport(
        matched_agents=matched_agents,
        expected_agents=len(baseline.agents),
        license_matches=license_matches,
        approval_matches=approval_matches,
        mismatches=tuple(mismatches),
    )


def _load_strict_yaml(path: Path) -> dict[str, Any]:
    import yaml

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValidationError(f"{path.name}: cannot read UTF-8 YAML: {error}") from error
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ValidationError(f"{path.name}: invalid YAML: {error}") from error
    if not isinstance(document, dict):
        raise ValidationError(f"{path.name}: document must be a mapping")
    return document


def validate_lineage_document(document: dict[str, Any]) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "src/schemas/provenance.schema.json"
    schema = _load_strict_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        raise ValidationError(f"{_field_path(list(error.absolute_path))}: {error.message}")
    for item in document["source_dispositions"]:
        if item["kind"] == "additive":
            if item["source_range"] is not None:
                raise ValidationError("additive requires source_range: null")
            if item["semantic_status"] != "additive":
                raise ValidationError("additive disposition requires semantic_status: additive")
        else:
            if item["source_range"] is None:
                raise ValidationError("source-derived requires source_range")
            if item["semantic_status"] == "additive":
                raise ValidationError("additive requires source_range: null")


def _parse_lineage(document: dict[str, Any]) -> Lineage:
    validate_lineage_document(document)
    dispositions: list[LineageDisposition] = []
    for item in document["source_dispositions"]:
        source_range = None
        if item["source_range"] is not None:
            source_range = SourceRange(
                start_line=item["source_range"]["start_line"],
                end_line=item["source_range"]["end_line"],
            )
        dispositions.append(
            LineageDisposition(
                kind=item["kind"],
                source_range=source_range,
                destination=LineageDestination(
                    type=item["destination"]["type"],
                    id=item["destination"]["id"],
                ),
                semantic_status=item["semantic_status"],
                design_authority=item.get("design_authority"),
            )
        )
    return Lineage(
        upstream_repository=document["upstream_repository"],
        upstream_commit=document["upstream_commit"],
        source_path=_strict_posix_path(document["source_path"], "source_path"),
        source_blob_sha256=document["source_blob_sha256"],
        dispositions=tuple(dispositions),
        source_license_spdx=document["source_license_spdx"],
        source_license_sha256=document["source_license_sha256"],
        source_attribution=document["source_attribution"],
        adaptation_version=document["adaptation_version"],
        target_id=document["target_id"],
        target_contract_id=document["target_contract_id"],
        procedure_ids=tuple(document["procedure_ids"]),
        skill_names=tuple(document["skill_names"]),
        resource_destinations=tuple(document["resource_destinations"]),
        approval_record=document["approval_record"],
    )


def load_lineage(root: Path, agent_id: str) -> Lineage:
    path = root / "provenance/lineage" / f"{agent_id}.yaml"
    if not path.is_file():
        raise ValidationError(f"lineage missing for agent: {agent_id}")
    return _parse_lineage(_load_strict_yaml(path))


def validate_partitions(lineage: Lineage, line_count: int) -> None:
    covered = [False] * (line_count + 1)
    for disposition in lineage.dispositions:
        if disposition.kind != "source-derived":
            continue
        assert disposition.source_range is not None
        start = disposition.source_range.start_line
        end = disposition.source_range.end_line
        if start > end:
            raise ValidationError(f"{lineage.target_id}: invalid range {start}-{end}")
        for line in range(start, end + 1):
            if line > line_count:
                raise ValidationError(
                    f"{lineage.target_id}: range {start}-{end} exceeds line_count {line_count}"
                )
            if covered[line]:
                raise ValidationError(
                    f"{lineage.target_id}: line {line} covered more than once"
                )
            covered[line] = True
    missing = [line for line in range(1, line_count + 1) if not covered[line]]
    if missing:
        raise ValidationError(
            f"{lineage.target_id}: uncovered lines: {missing[:5]}"
            + ("..." if len(missing) > 5 else "")
        )


def _destination_exists(root: Path, destination: LineageDestination) -> bool:
    if destination.type == "profile":
        return (root / "src/profiles" / f"{destination.id}.md").is_file()
    if destination.type == "skill":
        return (root / "src/skills" / destination.id / "SKILL.md").is_file()
    if destination.type == "contract":
        return True
    if destination.type in {"resource", "omission-record"}:
        return True
    return False


def verify_lineages(root: Path, baseline: SourceBaseline) -> tuple[str, ...]:
    mismatches: list[str] = []
    agent_index = {item.path.as_posix(): item for item in baseline.agents}
    lineage_dir = root / "provenance/lineage"
    if not lineage_dir.is_dir():
        return ("provenance/lineage: directory missing",)
    for path in sorted(lineage_dir.glob("*.yaml")):
        try:
            lineage = _parse_lineage(_load_strict_yaml(path))
        except ValidationError as error:
            mismatches.append(f"{path.name}: {error}")
            continue
        source_item = agent_index.get(lineage.source_path.as_posix())
        if source_item is None:
            mismatches.append(f"{path.name}: unknown source_path {lineage.source_path}")
            continue
        if lineage.source_blob_sha256 != source_item.sha256:
            mismatches.append(f"{path.name}: source_blob_sha256 mismatch")
        try:
            validate_partitions(lineage, source_item.line_count)
        except ValidationError as error:
            mismatches.append(str(error))
        for disposition in lineage.dispositions:
            if not _destination_exists(root, disposition.destination):
                mismatches.append(
                    f"{path.name}: missing destination "
                    f"{disposition.destination.type}:{disposition.destination.id}"
                )
    if len(list(lineage_dir.glob("*.yaml"))) != len(baseline.agents):
        mismatches.append(
            "provenance/lineage: expected "
            f"{len(baseline.agents)} files, found "
            f"{len(list(lineage_dir.glob('*.yaml')))}"
        )
    return tuple(mismatches)
