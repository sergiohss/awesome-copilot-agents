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


def load_baseline(root: Path) -> SourceBaseline:
    baseline_path = root / "provenance/source-baseline.json"
    schema_path = root / "src/schemas/source-baseline.schema.json"
    try:
        document = json.loads(baseline_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"source baseline: cannot load authority: {error}") from error
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
