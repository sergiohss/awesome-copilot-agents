from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from aca_tools.errors import ValidationError
from aca_tools.provenance import load_baseline, verify_upstream


PROJECT_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = Path("/var/www/projetos/awesome-claude-agents")
PINNED_COMMIT = "2050f3c60fcfea497f7b6b3ec6566cc316367a7e"
LICENSE_SHA256 = "6196817dde51dca830403aff706e50aa9929e53a80dc38a1b1636c5926574daa"
CLAUDE_SHA256 = "c2cc9e33425eedfe433d0699d0085e4548897fd33a33ca1cdf51b9b67990eeed"
CANONICAL_IDS = {
    "tech-lead-orchestrator", "project-analyst", "team-configurator",
    "code-archaeologist", "code-reviewer", "documentation-specialist",
    "performance-optimizer", "api-architect", "backend-developer",
    "frontend-developer", "tailwind-css-expert", "laravel-backend-expert",
    "laravel-eloquent-expert", "django-backend-expert", "django-api-developer",
    "django-orm-expert", "django-expert", "rails-backend-expert",
    "rails-api-developer", "rails-activerecord-expert", "react-component-architect",
    "react-nextjs-expert", "vue-component-architect", "vue-nuxt-expert",
    "vue-state-manager", "python-expert", "fastapi-expert", "ml-data-expert",
    "python-devops-cicd-expert", "python-performance-expert",
    "python-security-expert", "python-testing-expert", "python-web-scraping-expert",
}


def _git_blob(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{PINNED_COMMIT}:{path}"],
        cwd=SOURCE_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def test_baseline_schema_rejects_unknown_fields(tmp_path: Path):
    (tmp_path / "provenance").mkdir()
    (tmp_path / "src/schemas").mkdir(parents=True)
    document = json.loads((PROJECT_ROOT / "provenance/source-baseline.json").read_text())
    document["unexpected"] = True
    (tmp_path / "provenance/source-baseline.json").write_text(json.dumps(document))
    shutil.copy2(
        PROJECT_ROOT / "src/schemas/source-baseline.schema.json",
        tmp_path / "src/schemas/source-baseline.schema.json",
    )
    with pytest.raises(ValidationError, match=r"unexpected"):
        load_baseline(tmp_path)


def test_baseline_pins_all_source_blobs_license_and_approval_evidence():
    baseline = load_baseline(PROJECT_ROOT)
    assert baseline.upstream_repository == "https://github.com/vijaythecoder/awesome-claude-agents.git"
    assert baseline.upstream_commit == PINNED_COMMIT
    assert len(baseline.agents) == 33
    assert len({item.path for item in baseline.agents}) == 33

    for item in baseline.agents:
        blob = _git_blob(item.path.as_posix())
        assert hashlib.sha256(blob).hexdigest() == item.sha256
        assert len(blob.decode("utf-8").splitlines()) == item.line_count
        assert (SOURCE_ROOT / item.path).read_bytes() == blob

    assert baseline.license.spdx == "MIT"
    assert baseline.license.sha256 == LICENSE_SHA256
    assert hashlib.sha256(_git_blob("LICENSE")).hexdigest() == LICENSE_SHA256
    assert baseline.license.attribution == "Copyright (c) 2024 Awesome Claude Agents Contributors"
    assert baseline.approval.sha256 == CLAUDE_SHA256
    assert [(r.start_line, r.end_line) for r in baseline.approval.ranges] == [
        (101, 106), (189, 189)
    ]
    assert hashlib.sha256(_git_blob("CLAUDE.md")).hexdigest() == CLAUDE_SHA256

    report = verify_upstream(SOURCE_ROOT, baseline)
    assert report.ok, report.mismatches
    assert report.matched_agents == 33
    assert report.expected_agents == 33
    assert report.license_matches
    assert report.approval_matches


def test_identity_ledger_has_33_unique_ids_and_retains_source_defects():
    with (PROJECT_ROOT / "provenance/agents.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 33
    assert {row["canonical_id"] for row in rows} == CANONICAL_IDS
    assert len({row["source_path"] for row in rows}) == 33
    assert all(row["contract_id"] and row["lineage_path"] for row in rows)

    by_path = {row["source_path"]: row for row in rows}
    defects = {
        "agents/specialized/python/devops-cicd-expert.md": (
            "Python DevOps/CI-CD Expert", "python-devops-cicd-expert"
        ),
        "agents/specialized/python/performance-expert.md": (
            "Python Performance Expert", "python-performance-expert"
        ),
        "agents/specialized/python/security-expert.md": (
            "Python Security Expert", "python-security-expert"
        ),
        "agents/specialized/python/testing-expert.md": (
            "Python Testing Expert", "python-testing-expert"
        ),
        "agents/specialized/python/web-scraping-expert.md": (
            "Python Web Scraping Expert", "python-web-scraping-expert"
        ),
        "agents/specialized/vue/vue-state-manager.md": (
            "vue-component-architect", "vue-state-manager"
        ),
        "agents/universal/tailwind-css-expert.md": (
            "tailwind-frontend-expert", "tailwind-css-expert"
        ),
    }
    for path, (declared_name, canonical_id) in defects.items():
        assert by_path[path]["source_declared_name"] == declared_name
        assert by_path[path]["canonical_id"] == canonical_id
        assert by_path[path]["identity_disposition"] == "corrected:X-N"


def test_mutated_source_byte_reports_exact_path(tmp_path: Path):
    baseline = load_baseline(PROJECT_ROOT)
    for item in baseline.agents:
        destination = tmp_path / item.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / item.path, destination)
    shutil.copy2(SOURCE_ROOT / baseline.license.path, tmp_path / baseline.license.path)
    shutil.copy2(SOURCE_ROOT / baseline.approval.path, tmp_path / baseline.approval.path)
    (tmp_path / ".git").symlink_to(SOURCE_ROOT / ".git", target_is_directory=True)

    changed = baseline.agents[0].path
    changed_file = tmp_path / changed
    changed_file.write_bytes(changed_file.read_bytes() + b" ")

    report = verify_upstream(tmp_path, baseline)
    assert not report.ok
    assert report.mismatches == (
        f"{changed.as_posix()}: current bytes do not match pinned blob",
    )
