from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
SKILLS_ROOT = PROJECT_ROOT / "src/skills"
SECTIONS = ("When to use", "Workflow", "Checks", "Output", "References")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
PROC_00_09 = {f"PROC-{index:02d}" for index in range(10)}
PROC_10_20 = {f"PROC-{index:02d}" for index in range(10, 21)}


def _skill_dirs() -> list[Path]:
    return sorted(
        (path for path in SKILLS_ROOT.iterdir() if path.is_dir()),
        key=lambda item: item.name,
    )


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text)
    assert match, "SKILL.md must begin with YAML frontmatter"
    meta = yaml.safe_load(match.group(1))
    assert isinstance(meta, dict)
    return {str(key): str(value) for key, value in meta.items()}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(PROJECT_ROOT)


@pytest.fixture(scope="module")
def procedure_by_skill(catalog):
    return {procedure.skill_name: procedure for procedure in catalog.procedures}


def test_all_catalog_skills_materialized_once(procedure_by_skill):
    expected = set(procedure_by_skill)
    found = {path.name for path in _skill_dirs()}
    assert found == expected
    assert len(found) == 21


@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda path: path.name)
def test_skill_directory_matches_frontmatter_name(skill_dir: Path):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    assert meta.get("name") == skill_dir.name
    assert meta.get("description")
    assert "allowed-tools" not in meta
    for section in SECTIONS:
        assert f"## {section}" in text


@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda path: path.name)
def test_skill_references_exist_and_are_relative(skill_dir: Path):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("- references/"):
            continue
        relative = line.removeprefix("- ").strip()
        assert not relative.startswith("/")
        assert (skill_dir / relative).is_file()


@pytest.mark.parametrize(
    "procedure_id,skill_name",
    [
        (f"PROC-{index:02d}", procedure["skill_name"])
        for index, procedure in enumerate(
            yaml.safe_load(
                (PROJECT_ROOT / "src/catalog/procedures.yaml").read_text(encoding="utf-8")
            )["procedures"]
        )
    ],
    ids=lambda value: value[0],
)
def test_procedure_id_maps_to_exact_skill_name(procedure_id: str, skill_name: str, procedure_by_skill):
    procedure = next(item for item in procedure_by_skill.values() if item.id == procedure_id)
    assert procedure.skill_name == skill_name


@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda path: path.name)
def test_proc_00_09_core_workflow_skills(skill_dir: Path, procedure_by_skill):
    procedure = procedure_by_skill[skill_dir.name]
    if procedure.id not in PROC_00_09:
        pytest.skip("PROC-10+ covered elsewhere")
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "Handoff" in text or procedure.id != "PROC-09"


def test_core_orchestration_reference_contains_catalog_and_policies(catalog):
    catalog_ref = (
        SKILLS_ROOT / "aca-core-orchestration/references/catalog.md"
    ).read_text(encoding="utf-8")
    for agent in catalog.agents:
        assert f"`{agent.id}`" in catalog_ref
        assert f"`{agent.contract_id}`" in catalog_ref
    assert "Dangling-edge substitutions" in catalog_ref
    assert "Two-agent policy" in catalog_ref
    assert "Surface fallbacks" in catalog_ref
    contracts_ref = (
        SKILLS_ROOT / "aca-core-orchestration/references/contracts.md"
    ).read_text(encoding="utf-8")
    for contract_id in catalog.contracts:
        assert f"`{contract_id}`" in contracts_ref


def test_proc_10_20_domain_skills_include_required_keywords():
    expectations = {
        "aca-orm-query-optimization": ("before", "after", "migration"),
        "aca-performance-optimization-lifecycle": ("baseline", "regression"),
        "aca-severity-based-code-review": ("PASS", "BLOCK", "severity"),
        "aca-documentation-gap-closure": ("changelog", "audience"),
        "aca-accessible-ui-delivery": ("accessibility", "fallback"),
        "aca-test-strategy-design": ("risk", "pytest"),
        "aca-secure-code-assessment": ("read-only", "remediation"),
        "aca-deployment-safety-pipeline": ("rollback", "rollout"),
        "aca-reproducible-ml-lifecycle": ("reproduc", "metadata"),
        "aca-authorized-scraping-pipeline": ("authorization", "robots"),
        "aca-bounded-instruction-update": ("generated block", "AP-X"),
    }
    for skill_name, tokens in expectations.items():
        text = (SKILLS_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8").lower()
        for token in tokens:
            assert token.lower() in text, f"{skill_name} missing {token}"


def test_generated_packages_include_all_skills_once():
    manifests = [
        PROJECT_ROOT / "packages/manifests/repository.json",
        PROJECT_ROOT / "packages/manifests/user-cli.json",
        PROJECT_ROOT / "packages/manifests/user-vscode.json",
    ]
    catalog = load_catalog(PROJECT_ROOT)
    expected = {procedure.skill_name for procedure in catalog.procedures}
    for manifest_path in manifests:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_paths = [
            entry["path"]
            for entry in document["files"]
            if entry["path"].endswith("/SKILL.md")
            and (
                "/skills/" in entry["path"]
                or entry["path"].startswith("skills/")
            )
        ]
        names = {Path(path).parts[-2] for path in skill_paths}
        assert names == expected
