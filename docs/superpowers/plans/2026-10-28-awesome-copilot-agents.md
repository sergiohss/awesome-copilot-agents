# Awesome Copilot Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/var/www/projetos/awesome-copilot-agents` as a deterministic, auditable GitHub Copilot distribution containing exactly 33 agent profiles and 21 shared Agent Skills for repository, Copilot CLI user, and VS Code user installation.

**Architecture:** Canonical YAML catalogs, concise Markdown profile bodies, reusable fragments, typed JSON Schemas, skills, instructions, and exact provenance are the only editable semantic inputs. A Python build tool validates those inputs, renders all checked-in distributions transactionally, records content digests, and rejects drift. A collision-safe installer consumes generated package manifests; no generated profile contains runtime build references.

**Tech Stack:** Python 3.11+, PyYAML 6.0.2, jsonschema 4.23.0, pytest 8.3.5, Markdown/YAML/JSON Schema, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-28-awesome-copilot-agents-design.md`

## Global Constraints

- Work in the separate repository `/var/www/projetos/awesome-copilot-agents`; never add generated Copilot assets to the Claude source repository.
- Preserve source baseline `2050f3c60fcfea497f7b6b3ec6566cc316367a7e` and MIT attribution.
- Expose exactly 33 canonical public agent IDs from spec §7 and exactly PROC-00–PROC-20 with the exact skill names from spec §8.
- Portable profile frontmatter contains only `name`, `description`, and explicit `tools`.
- Static tool aliases are limited to `read`, `search`, `agent`, `edit`, and `execute`; each row uses T-R, T-RX, T-O, T-E, or T-W exactly as specified.
- Generated profiles warn above 8,000 Unicode scalar values and fail above 12,000; the official platform ceiling is 30,000 characters.
- Generation uses UTF-8, NFC, LF, stable lexical ordering, no timestamps, no absolute paths, no environment-derived text, and no network-fetched text.
- GitHub.com coding-agent orchestration returns Route Plan v1 and requires separately selected sessions; it never claims subagent execution.
- At most two independent agents run concurrently on VS Code or CLI orchestration surfaces.
- `VUE-03-SEMANTIC-REPAIR` is the only additive design authority; all Vue state behavior uses `source_range: null`.
- CAPTCHA, anti-bot, access-control, or detection evasion is `omitted-for-safety`; replacement behavior requires authorization, API preference, terms/robots review, rate controls, and credential approval.
- Prompts and canonical technical identifiers are English. Reader and installation documentation is complete in English and pt-BR.
- Repository and user packages are supported only where the spec documents them; do not create personal-cloud, organization, or enterprise packages.
- Every task ends with its focused tests and one commit. Do not combine task commits.

## Review Focus

1. **Unicode normalization and scalar counting:** NFD input and astral characters must render as NFC and be counted across complete profile frontmatter plus body; Task 2 pins this.
2. **Unknown catalog/frontmatter capability:** an unknown tool or key must fail before any generated tree changes; Tasks 1–2 pin this.
3. **User-modified generated file:** reinstall/uninstall must refuse silent replacement or deletion and report the exact digest mismatch; Task 14 pins this.
4. **Install path containing spaces:** planning, copy, upgrade, and uninstall must use path APIs without shell interpolation and stay inside the selected root; Task 14 pins this.
5. **Unavailable cloud subagent/browser/MCP capability:** profiles must return the documented fallback without impersonation or fabricated evidence; Tasks 3 and 15 pin this.

---

### Task 1: Repository Bootstrap, Immutable Source Authority, and Strict Catalog Loader

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/.gitignore`
- Create: `/var/www/projetos/awesome-copilot-agents/pyproject.toml`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/__init__.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/errors.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/models.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/loaders.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/provenance.py`
- Create: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/catalog/procedures.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/catalog/contracts.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/catalog/instructions.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/instructions/copilot.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/catalog.schema.json`
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/source-baseline.schema.json`
- Create: `/var/www/projetos/awesome-copilot-agents/provenance/source-baseline.json`
- Create: `/var/www/projetos/awesome-copilot-agents/provenance/agents.csv`
- Create: `/var/www/projetos/awesome-copilot-agents/scripts/verify_upstream.py`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/design/architecture.md`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_catalog.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/conftest.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_baseline.py`

**Interfaces:**
- Consumes: approved spec at `/var/www/projetos/awesome-claude-agents/docs/superpowers/specs/2026-10-28-awesome-copilot-agents-design.md` and source blobs at commit `2050f3c60fcfea497f7b6b3ec6566cc316367a7e`.
- Produces: `aca_tools.models.Catalog`; `aca_tools.loaders.load_catalog(root: Path) -> Catalog`; `aca_tools.provenance.load_baseline(root: Path) -> SourceBaseline`; `aca_tools.provenance.verify_upstream(source_root: Path, baseline: SourceBaseline) -> VerificationReport`; `aca_tools.errors.ValidationError`; immutable baseline/package metadata; 33-row source-to-canonical identity authority; strict canonical YAML skeletons used by every later task.

- [ ] **Step 1: Initialize the separate repository and copy the approved architecture**

Run:

```bash
mkdir -p /var/www/projetos/awesome-copilot-agents
cd /var/www/projetos/awesome-copilot-agents
git init -b main
mkdir -p docs/design
cp /var/www/projetos/awesome-claude-agents/docs/superpowers/specs/2026-10-28-awesome-copilot-agents-design.md docs/design/architecture.md
```

Expected: a new `main` repository exists; the source repository remains unchanged.

- [ ] **Step 2: Write the failing strict-loader tests**

```python
from pathlib import Path
import pytest
from aca_tools.errors import ValidationError
from aca_tools.loaders import load_catalog


def test_catalog_rejects_unknown_tool(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, tools=["read", "teleport"])
    with pytest.raises(ValidationError, match=r"agents\[0\]\.tools\[1\].*teleport"):
        load_catalog(tmp_path)


def test_catalog_rejects_unknown_agent_key(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, extra_agent={"temperature": 0.2})
    with pytest.raises(ValidationError, match=r"temperature"):
        load_catalog(tmp_path)


def test_catalog_requires_unique_public_ids(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, duplicate_agent=True)
    with pytest.raises(ValidationError, match=r"duplicate agent id: project-analyst"):
        load_catalog(tmp_path)
```

In `tests/test_baseline.py`, assert the baseline schema rejects unknown fields; all 33 source paths and blobs exist at the pinned commit; current source-agent bytes match those blobs; the license hash is exact; root `CLAUDE.md` has the approved hash/ranges; and `agents.csv` has 33 unique canonical IDs with original filename/name defects retained. Mutating one source byte must make verification fail with its exact path.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]' && .venv/bin/python -m pytest tests/test_catalog.py tests/test_baseline.py -q`

Expected: FAIL because catalog/baseline loader modules, authoritative artifacts, verifier, and fixtures do not exist.

- [ ] **Step 4: Implement immutable models, strict catalog loading, and source authority**

Use these public signatures:

```python
@dataclass(frozen=True, slots=True)
class AgentSpec:
    id: str
    description: str
    tools: tuple[str, ...]
    tool_policy: str
    approval_policy: str
    risk_gates: tuple[str, ...]
    surfaces: tuple[str, ...]
    contract_id: str
    procedure_ids: tuple[str, ...]
    profile: PurePosixPath
    fragments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProcedureSpec:
    id: str
    skill_name: str
    contract: str

@dataclass(frozen=True, slots=True)
class InstructionCatalog:
    repository: PurePosixPath
    path_specific: tuple[Mapping[str, object], ...]



@dataclass(frozen=True, slots=True)
class Catalog:
    agents: tuple[AgentSpec, ...]
    procedures: tuple[ProcedureSpec, ...]
    contracts: Mapping[str, str]
    instructions: InstructionCatalog


def load_catalog(root: Path) -> Catalog:
    """Load four canonical catalogs, validate JSON Schema, cross-links, IDs, and static tools."""
```

Add strict `SourceBaseline` models and implement `load_baseline`/`verify_upstream`. `source-baseline.json` is the only source for upstream repository, commit, per-file path/line-count/blob SHA-256, MIT SPDX/hash/attribution, and the root `CLAUDE.md` approval hash/ranges. Populate `agents.csv` with all 33 source paths, original declared names (including malformed/colliding values), canonical IDs, contracts, identity dispositions, and future lineage paths. Build it from the approved spec and blobs read with `git show 2050f3c60fcfea497f7b6b3ec6566cc316367a7e:<path>`; compare the current source-agent bytes to those blobs before any conversion. No later task may duplicate or silently rewrite these values.

Run: `.venv/bin/python scripts/verify_upstream.py --source-root /var/www/projetos/awesome-claude-agents --record-baseline`

Expected: 33/33 current source-agent blobs, MIT license, and root approval evidence match the pinned commit; baseline and identity ledger are written deterministically.

`load_catalog` must use `yaml.safe_load`, reject YAML aliases/custom tags, reject unknown keys through JSON Schema `additionalProperties: false`, enforce POSIX relative paths, enforce the five static tool-policy expansions, and report a deterministic dotted field path.

`src/catalog/agents.yaml` starts as `agents: []`; `procedures.yaml` contains all 21 exact PROC/name pairs from spec §8 so profile cross-links can be validated while skill bodies are added in Tasks 11–12; `contracts.yaml` starts as `contracts: {}`; `instructions.yaml` contains `repository: src/instructions/copilot.md` and `path_specific: []`. Write `src/instructions/copilot.md` now with the complete baseline rules to prefer exact specialists, load packaged skills progressively, preserve approval gates, and never impersonate unavailable tools or roles; Task 3 extends it only with the finalized contract/surface wording. `tests/conftest.py` supplies `minimal_catalog_tree` by writing complete four-file fixture catalogs under `tmp_path`; it never mutates repository canonical inputs.

- [ ] **Step 5: Run the focused tests**

Run: `.venv/bin/python -m pytest tests/test_catalog.py tests/test_baseline.py -q && .venv/bin/python scripts/verify_upstream.py --source-root /var/www/projetos/awesome-claude-agents --baseline-only`

Expected: catalog and baseline tests PASS; immutable upstream verification reports 33/33 plus license and approval lineage.

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml aca_tools src/catalog src/instructions/copilot.md src/schemas/catalog.schema.json src/schemas/source-baseline.schema.json provenance scripts/verify_upstream.py docs/design tests/conftest.py tests/test_catalog.py tests/test_baseline.py
git commit -m "build: add canonical catalog and source baseline"
```

---

### Task 2: Deterministic Transactional Generator

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/render.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/manifest.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/generate.py`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/cli.py`
- Create: `/var/www/projetos/awesome-copilot-agents/scripts/generate.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/fixtures/minimal/provenance/source-baseline.json`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/fixtures/minimal/pyproject.toml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/fixtures/minimal/src/profiles/project-analyst.md`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/fixtures/minimal/src/fragments/ins-core.md`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_generation.py`
- Modify: `/var/www/projetos/awesome-copilot-agents/tests/conftest.py`

**Interfaces:**
- Consumes: `Catalog`, canonical profile/fragment/skill/instruction trees.
- Produces: `render_profile(agent: AgentSpec, body: str, fragments: Sequence[str]) -> str`; `build_outputs(root: Path, *, require_complete: bool = False) -> dict[PurePosixPath, bytes]`; `generate(root: Path, *, check: bool = False, require_complete: bool = False) -> GenerationReport`; SHA-256 package manifests.

- [ ] **Step 1: Write failing determinism, Unicode, limit, and rollback tests**

```python
def test_render_normalizes_nfc_and_counts_complete_profile(minimal_project):
    minimal_project.profile.write_text("Cafe\u0301 😀", encoding="utf-8")
    output = build_outputs(minimal_project.root)[PurePosixPath(".github/agents/project-analyst.agent.md")]
    text = output.decode("utf-8")
    assert "Café 😀" in text
    assert unicodedata.is_normalized("NFC", text)
    assert len(text) == GenerationReport.scalar_count(text)


def test_unknown_tool_fails_without_changing_existing_output(minimal_project):
    existing = minimal_project.output.read_bytes()
    minimal_project.set_tools(["read", "teleport"])
    with pytest.raises(ValidationError, match="teleport"):
        generate(minimal_project.root)
    assert minimal_project.output.read_bytes() == existing


def test_second_generation_is_byte_identical(minimal_project):
    first = generate(minimal_project.root)
    snapshot = {path: path.read_bytes() for path in first.written_paths}
    second = generate(minimal_project.root)
    assert second.changed_paths == ()
    assert snapshot == {path: path.read_bytes() for path in first.written_paths}
```

Also pin a profile of 8,001 scalar values to one warning and a profile of 12,001 values to a hard failure before writes.
Add `test_release_mode_rejects_incomplete_catalog`: the default development build may render a strict internally consistent subset, but `require_complete=True` must reject anything other than 33 profiles and 21 materialized skills. Both modes reject broken references, unknown tools, invalid schemas, and missing files declared by a present row.

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_generation.py -q`

Expected: FAIL because generator interfaces do not exist.

- [ ] **Step 3: Implement stable rendering and manifests**

Render exact portable frontmatter without comments:

```python
def render_profile(agent: AgentSpec, body: str, fragments: Sequence[str]) -> str:
    description = json.dumps(agent.description, ensure_ascii=False)
    tools = ", ".join(agent.tools)
    sections = [body.strip(), *(fragment.strip() for fragment in fragments)]
    rendered = f"---\nname: {agent.id}\ndescription: {description}\ntools: [{tools}]\n---\n\n" + "\n\n".join(sections) + "\n"
    return unicodedata.normalize("NFC", rendered).replace("\r\n", "\n").replace("\r", "\n")
```

Reject surrogate code points. Count Python Unicode code points over the final string. Build repository outputs, byte-equivalent portable repository package, CLI user package, VS Code import package, and four sorted JSON manifests. Load source metadata only from `provenance/source-baseline.json` and adaptation version only from `pyproject.toml`; never duplicate those constants in generator code. Each manifest has `schema_version`, `package_id`, `adaptation_version`, `complete`, `upstream_repository`, `upstream_commit`, `license_spdx`, `source_attribution`, and sorted `files`; file entries use `{path, sha256, size}` and package-relative POSIX paths. The metadata is the package-level attribution required by spec §11 and must never be injected into agent profiles.
Development mode exists only to make category commits testable while canonical content is being added; generated manifests record `complete: false`. CLI `--release` maps to `require_complete=True`, requires exactly 33 agent rows/files and all 21 cataloged skill directories, and records `complete: true`. Task 12 switches the checked-in distributions to complete release mode. Release validation always invokes `--release`; there is no environment variable or manifest field that can bypass it.

- [ ] **Step 4: Implement transactional replacement**

Stage every owned target under a temporary directory in the destination filesystem. Validate the complete stage, move existing owned roots to a backup directory, move staged roots into place, and restore all backups if any replacement fails. Owned roots are `.github/agents`, `.github/skills`, `.github/instructions`, `.github/copilot-instructions.md`, `packages/repository/portable`, `packages/user/cli`, `packages/user/vscode`, and `packages/manifests`. Never replace `.github/workflows`.

- [ ] **Step 5: Run the focused tests twice**

Run: `.venv/bin/python -m pytest tests/test_generation.py -q && .venv/bin/python scripts/generate.py && .venv/bin/python scripts/generate.py --check`

Expected: tests PASS; second generation reports zero changed paths.

- [ ] **Step 6: Commit**

```bash
git add aca_tools scripts/generate.py tests/fixtures/minimal tests/test_generation.py .github packages
git commit -m "build: add deterministic Copilot distribution generator"
```

---

### Task 3: Contracts, Shared Fragments, Instructions, and Routing Fixtures

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/handoff-v1.schema.json`
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/route-plan-v1.schema.json`
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/result-contracts.schema.json`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/contracts.py`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/ins-core.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/approval-orchestrated-complex.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/approval-bounded-request-is-authorization.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/approval-explicit-before-external-side-effect.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/approval-review-only.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/handoff-v1.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/fragments/surface-fallback.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/instructions/copilot.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/cross-cutting.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_contracts.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_surface_fallbacks.py`

**Interfaces:**
- Consumes: contract IDs from spec §7 and Handoff/Route Plan fields from spec §9.
- Produces: `validate_handoff(agent_id: str, payload: Mapping[str, object], catalog: Catalog) -> None`; shared fragments injected by Task 2; cross-cutting route fixtures consumed by Task 15.

- [ ] **Step 1: Write failing schema tests**

Pin: all 33 primary contract IDs exist; Handoff v1 rejects missing `status`; `routing.recommended_next_agent` rejects IDs outside the catalog; route-plan concurrency groups reject three agents; cloud mode rejects a claim that a subagent executed; unavailable browser/MCP requires an explicit unavailable-evidence field or `blocked` status.

Use this valid envelope in the positive test:

```python
VALID = {
    "handoff_version": 1,
    "contract_id": "stack-analysis-v1",
    "status": "completed",
    "summary": "Detected Python and FastAPI from pyproject.toml.",
    "artifact_paths": [],
    "routing": {"recommended_next_agent": "fastapi-expert", "reason": "Exact framework owner", "prerequisites": []},
    "result": {"stack": ["Python", "FastAPI"], "confidence": "high", "unknowns": []},
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_contracts.py tests/test_surface_fallbacks.py -q`

Expected: FAIL because schemas and fragments do not exist.

- [ ] **Step 3: Define all exact primary contracts**

Add these `$defs` to `result-contracts.schema.json` and map them in `contracts.yaml`: `route-plan-v1`, `stack-analysis-v1`, `team-configuration-v1`, `codebase-assessment-v1`, `code-review-v1`, `documentation-changelog-v1`, `performance-report-v1`, `api-design-report-v1`, `backend-implementation-v1`, `frontend-implementation-v1`, `component-delivery-v1`, `laravel-implementation-v1`, `eloquent-work-summary-v1`, `django-backend-implementation-v1`, `django-api-implementation-v1`, `django-orm-optimization-v1`, `django-fullstack-implementation-v1`, `rails-backend-implementation-v1`, `rails-api-implementation-v1`, `rails-activerecord-optimization-v1`, `react-component-delivery-v1`, `nextjs-implementation-v1`, `vue-implementation-v1`, `nuxt-implementation-v1`, `vue-state-delivery-v1`, `python-implementation-v1`, `fastapi-implementation-v1`, `ml-data-implementation-v1`, `python-deployment-delivery-v1`, `python-performance-report-v1`, `python-security-assessment-v1`, `python-testing-delivery-v1`, and `python-acquisition-report-v1`.

Each `$def` requires the consumer-visible fields named in spec §7; set `additionalProperties: false` at every object boundary. Handoff `status` is exactly `completed`, `blocked`, or `needs-approval`.

- [ ] **Step 4: Write the seven exact fragments and repository instruction**

`ins-core.md` defines evidence-first behavior, exact-agent precedence, no role impersonation, truthful capability reporting, and artifact paths. The four approval fragments encode AP-OC/AP-B/AP-X/AP-R verbatim from spec §6.2. `surface-fallback.md` distinguishes VS Code, CLI, and cloud and caps delegation at two. `handoff-v1.md` includes the complete envelope and instructs agents to validate `result` against their one primary contract. `copilot.md` tells Copilot to prefer exact specialists, discover packaged skills progressively, and preserve approvals.

- [ ] **Step 5: Run focused tests and regenerate owned distributions**

Run: `.venv/bin/python -m pytest tests/test_contracts.py tests/test_surface_fallbacks.py -q && .venv/bin/python scripts/generate.py && .venv/bin/python scripts/generate.py --check`

Expected: tests PASS; generated repository instructions, portable copies, and manifests include the finalized canonical instruction; the check reports zero changed paths.

- [ ] **Step 6: Commit**

```bash
git add aca_tools/contracts.py src/catalog/contracts.yaml src/schemas src/fragments src/instructions src/routing-fixtures/cross-cutting.yaml tests/test_contracts.py tests/test_surface_fallbacks.py .github packages
git commit -m "feat: define handoff contracts and surface policies"
```

---

### Task 4: Orchestrator Profiles

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/tech-lead-orchestrator.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/project-analyst.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/team-configurator.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/orchestrators.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_orchestrators.py`

**Interfaces:**
- Consumes: source files `agents/orchestrators/tech-lead-orchestrator.md`, `agents/orchestrators/project-analyst.md`, `agents/orchestrators/team-configurator.md`; shared fragments and contracts.
- Produces: canonical profiles `tech-lead-orchestrator`, `project-analyst`, `team-configurator`; route-plan and stack/configuration behavior.

- [ ] **Step 1: Write failing catalog and routing tests**

Assert exact rows: tech lead uses T-O/AP-OC, `route-plan-v1`, PROC-00/03/04/05; project analyst uses T-RX/AP-R, `stack-analysis-v1`, PROC-01/02; team configurator uses T-E/AP-X, `team-configuration-v1`, PROC-01/02/05/20, manual selection. Assert a bounded FastAPI implementation request excludes the tech lead, while a multi-stack architecture request selects it. Assert cloud route plans contain `cloud-separate-session` and no execution claim.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_orchestrators.py -q`

Expected: FAIL because the three rows and profiles are absent.

- [ ] **Step 3: Adapt the three profile bodies**

Each body has `Role`, `Use when`, `Do not use when`, `Workflow`, `Surface behavior`, and `Result contract` sections. Tech lead performs research → approval digest → route plan and never implements slices. Project analyst inventories files before stack conclusions and returns confidence/unknowns. Team configurator requires existing stack evidence, previews only its generated instruction block, and obtains AP-X before mutation. Remove `@agent-*`, Claude paths, `model`, `LS`, `WriteFile`, and unsupported tool promises.

- [ ] **Step 4: Add positive, exclusion, precedence, manual, and cloud fixtures**

Every fixture names exact expected ID, excluded alternatives, approval policy, contract, surface mode, and expected status. Include a three-slice plan split into concurrency groups of two and one.

- [ ] **Step 5: Generate and run focused tests**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_orchestrators.py -q`

Expected: three generated profiles; tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/orchestrators.yaml .github packages tests/test_orchestrators.py
git commit -m "feat: add Copilot orchestrator profiles"
```

---

### Task 5: Core Review, Archaeology, Documentation, and Performance Profiles

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/code-archaeologist.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/code-reviewer.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/documentation-specialist.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/performance-optimizer.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/core.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_core_profiles.py`

**Interfaces:**
- Consumes: four `agents/core/*.md` source profiles.
- Produces: exact core rows and typed results `codebase-assessment-v1`, `code-review-v1`, `documentation-changelog-v1`, `performance-report-v1`.

- [ ] **Step 1: Write failing parameterized row tests**

Pin exact `(id, tools, approval, contract, procedures)` tuples:

```python
CORE = [
    ("code-archaeologist", ("read", "search", "execute"), "AP-R", "codebase-assessment-v1", ("PROC-01", "PROC-02", "PROC-07", "PROC-16")),
    ("code-reviewer", ("read", "search", "execute"), "AP-R", "code-review-v1", ("PROC-12", "PROC-16")),
    ("documentation-specialist", ("read", "search", "edit", "execute"), "AP-B", "documentation-changelog-v1", ("PROC-13",)),
    ("performance-optimizer", ("read", "search", "edit", "execute"), "AP-B", "performance-report-v1", ("PROC-11",)),
]
```

Also assert review is read-only and cannot silently remediate; destructive load testing requires its risk gate.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_core_profiles.py -q`

Expected: FAIL because rows are absent.

- [ ] **Step 3: Adapt the four bodies and fixtures**

Preserve the archaeologist's 11 assessment sections, reviewer severity/evidence/PASS-or-BLOCK output, documentation audience/gap/artifact/changelog flow, and performance baseline/profile/change/compare lifecycle. Scope exact ORM and Python runtime requests to their narrower specialists.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_core_profiles.py -q`

Expected: seven total generated profiles; focused tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/core.yaml .github packages tests/test_core_profiles.py
git commit -m "feat: add Copilot core specialist profiles"
```

---

### Task 6: Universal Fallback Profiles

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/api-architect.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/backend-developer.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/frontend-developer.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/tailwind-css-expert.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/universal.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_universal_profiles.py`

**Interfaces:**
- Consumes: four `agents/universal/*.md` source profiles.
- Produces: API design and three universal fallback profiles; specialist-first precedence fixtures.

- [ ] **Step 1: Write failing precedence tests**

Assert all four use T-W/AP-B and exact contracts/procedures from spec §7. Assert a Django REST request selects `django-api-developer`, not `api-architect` or `backend-developer`; a generic unknown backend request selects `backend-developer`; React/Vue requests exclude `frontend-developer`; Tailwind-only work selects `tailwind-css-expert`.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_universal_profiles.py -q`

Expected: FAIL.

- [ ] **Step 3: Adapt bodies with explicit fallback boundaries**

API architect produces a validated OpenAPI/GraphQL contract before implementation. Backend and frontend profiles state they are fallbacks only when no exact framework owner exists. Tailwind profile owns utility/theme work, requires accessibility/visual evidence when available, and reports capability absence rather than claiming browser output.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_universal_profiles.py -q`

Expected: 11 total generated profiles; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/universal.yaml .github packages tests/test_universal_profiles.py
git commit -m "feat: add universal Copilot fallback profiles"
```

---

### Task 7: Laravel, Django, and Rails Profiles

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/laravel-backend-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/laravel-eloquent-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/django-backend-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/django-api-developer.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/django-orm-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/rails-backend-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/rails-api-developer.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/rails-activerecord-expert.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/backend-frameworks.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_backend_framework_profiles.py`

**Interfaces:**
- Consumes: all files under `agents/specialized/laravel`, `agents/specialized/django`, and `agents/specialized/rails`.
- Produces: eight framework profiles with application/API/ORM precedence and migration risk gates.

- [ ] **Step 1: Write failing ownership matrix tests**

For each framework, pin application logic → backend expert, API/auth/serialization → API developer where present, query/schema/index bottleneck → ORM expert. Laravel API design routes first to `api-architect`, then `laravel-backend-expert`; it never emits dangling `laravel-api-architect`. Destructive migrations return `needs-approval` before execution.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_backend_framework_profiles.py -q`

Expected: FAIL.

- [ ] **Step 3: Adapt all eight bodies**

Retain framework-specific conventions, installed-version-first documentation, repository convention scans, typed file/artifact results, security checks, and test evidence. Move reusable contract-first API, ORM optimization, and handoff procedures to PROC-08/10/09 references while leaving a self-contained minimum workflow in every profile.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_backend_framework_profiles.py -q`

Expected: 19 total generated profiles; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/backend-frameworks.yaml .github packages tests/test_backend_framework_profiles.py
git commit -m "feat: add Laravel Django and Rails Copilot profiles"
```

---

### Task 8: React, Next.js, Vue, Nuxt, and Repaired Vue State Profile

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/react-component-architect.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/react-nextjs-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/vue-component-architect.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/vue-nuxt-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/vue-state-manager.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/frontend-frameworks.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_frontend_framework_profiles.py`

**Interfaces:**
- Consumes: all files under `agents/specialized/react` and `agents/specialized/vue`; approved additive authority `VUE-03-SEMANTIC-REPAIR`.
- Produces: five UI profiles and exact component/framework/state precedence.

- [ ] **Step 1: Write failing framework and semantic-repair tests**

Pin React components/hooks/design systems to `react-component-architect`, Next routing/render/cache/server actions to `react-nextjs-expert`, Vue components/composables to `vue-component-architect`, Nuxt/Nitro/SSR/SEO to `vue-nuxt-expert`, and Pinia/Vuex/persistence/SSR hydration/migration to `vue-state-manager`. Assert the state result requires stores, actions/getters, data flow, persistence/hydration, migration, consumers, tests, and files.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_frontend_framework_profiles.py -q`

Expected: FAIL.

- [ ] **Step 3: Adapt four derived profiles and author the approved state profile**

Derived profiles preserve source behavior and use PROC-06/07/09/14. The state profile must not claim its Pinia/Vuex semantics came from duplicated source lines. Its body states the approved scope: store boundaries, actions/getters/data-flow contracts, persistence, SSR hydration, Vuex-to-Pinia migration, tests, consumers, and integration reporting. Browser/MCP absence is an explicit limitation, not fabricated visual evidence.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_frontend_framework_profiles.py -q`

Expected: 24 total generated profiles; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/frontend-frameworks.yaml .github packages tests/test_frontend_framework_profiles.py
git commit -m "feat: add React and repaired Vue Copilot profiles"
```

---

### Task 9: Python, FastAPI, Django Full-Stack, and ML/Data Profiles

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/python-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/fastapi-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/django-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/ml-data-expert.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/python-application.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_python_application_profiles.py`

**Interfaces:**
- Consumes: `agents/specialized/python/python-expert.md`, `fastapi-expert.md`, `django-expert.md`, `ml-data-expert.md`.
- Produces: four translated English profiles with exact corrected IDs and application/data boundaries.

- [ ] **Step 1: Write failing corrected-ID and routing tests**

Assert only `python-expert`, `fastapi-expert`, `django-expert`, and `ml-data-expert` appear; no filename-era alias is public. FastAPI/Pydantic/async selects FastAPI; cross-cutting Django templates/admin/DRF/Celery selects full-stack Django; general Python selects Python; training/serving/data lifecycle selects ML/data and gates external data/model side effects.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_python_application_profiles.py -q`

Expected: FAIL.

- [ ] **Step 3: Translate and reduce the four French manuals**

Keep domain workflows, version-aware docs, security/performance constraints, measurable evidence, and result fields. Move long snippets, version tables, checklists, and examples into later skill resources; do not copy Claude invocation syntax or model settings. Every profile remains useful without loading a skill.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_python_application_profiles.py -q`

Expected: 28 total generated profiles; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/python-application.yaml .github packages tests/test_python_application_profiles.py
git commit -m "feat: add Python application and ML Copilot profiles"
```

---

### Task 10: Python DevOps, Performance, Security, Testing, and Authorized Acquisition Profiles

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/python-devops-cicd-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/python-performance-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/python-security-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/python-testing-expert.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/profiles/python-web-scraping-expert.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/src/catalog/agents.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/src/routing-fixtures/python-operations.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_python_operations_profiles.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_safety.py`

**Interfaces:**
- Consumes: `devops-cicd-expert.md`, `performance-expert.md`, `security-expert.md`, `testing-expert.md`, `web-scraping-expert.md` from `agents/specialized/python`.
- Produces: five corrected `python-*` identities, read-only security assessment, explicit external-action gates, and safe authorized acquisition.

- [ ] **Step 1: Write failing identity, risk, and banned-content tests**

Assert exact IDs and contracts from spec §7. DevOps is manual with AP-X for deploy/credentials/infrastructure. Security uses T-RX/AP-R and never remediates in the same assignment. Acquisition is manual and AP-X; missing authorization returns `needs-approval`. Scan every canonical and generated file case-insensitively for forbidden bypass semantics: CAPTCHA solving, stealth plugins, fingerprint spoofing, access-control bypass, bot-detection evasion, and credential theft. Also reject `@agent-`, `~/.claude`, `model: opus`, `WriteFile`, `WebFetch`, and `Context7`.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_python_operations_profiles.py tests/test_safety.py -q`

Expected: FAIL.

- [ ] **Step 3: Translate four profiles and safely rewrite acquisition**

DevOps retains CI/CD, containers, IaC, rollout, rollback, credential and infrastructure gates. Performance requires profiler evidence and before/after regression disposition. Security returns scope/assets/threats/severity/evidence/controls/remediation/verification/disposition but performs no fix. Testing returns risk map/layers/fixtures/files/commands/coverage/mutation/gaps. Acquisition starts with written authorization, prefers APIs, reviews terms/robots, applies respectful rate controls, records lineage, and explicitly refuses bypass/evasion.

- [ ] **Step 4: Generate and test all 33 identities**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_python_operations_profiles.py tests/test_safety.py -q`

Expected: exactly 33 generated agent files, 33 unique `name` values, no forbidden content, tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/catalog/agents.yaml src/profiles src/routing-fixtures/python-operations.yaml .github packages tests/test_python_operations_profiles.py tests/test_safety.py
git commit -m "feat: add safe Python operations Copilot profiles"
```

---

### Task 11: Core Workflow Skills PROC-00–PROC-09

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-core-orchestration/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-inventory-first-discovery/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-stack-detection-with-confidence/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-deterministic-agent-routing/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-human-approval-checkpoint/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-specialist-first-selection/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-version-aware-official-docs/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-existing-convention-scan/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-contract-first-api-design/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-structured-implementation-handoff/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-core-orchestration/references/catalog.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-core-orchestration/references/contracts.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-deterministic-agent-routing/references/precedence.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-contract-first-api-design/references/checklist.md`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_skills.py`

**Interfaces:**
- Consumes: procedure catalog and repeated source workflows extracted from all 33 source files.
- Produces: ten progressively disclosed Agent Skills with exact names and portable `SKILL.md` frontmatter.

- [ ] **Step 1: Write failing skill discovery tests**

Assert directory name equals frontmatter `name`; description states trigger conditions; no skill uses `allowed-tools`; PROC ID/name mapping is exact; references are relative and exist; core orchestration reference contains all 33 IDs, exact contracts, dangling-edge substitutions, surface fallbacks, and two-agent policy.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_skills.py -q -k 'proc_00_09 or core_orchestration'`

Expected: FAIL because skills are absent.

- [ ] **Step 3: Author concise entry skills and references**

Each `SKILL.md` contains only YAML `name` and `description`, then `When to use`, `Workflow`, `Checks`, `Output`, and `References`. PROC-00 carries orchestration contracts; PROC-01/02 evidence inventory and confidence; PROC-03/05 deterministic specialist precedence; PROC-04 approve/revise/stop; PROC-06 local-version/docs-first; PROC-07 convention scan; PROC-08 contract-first API; PROC-09 Handoff v1. Large matrices live in the four exact reference files above.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py && .venv/bin/python -m pytest tests/test_skills.py -q -k 'proc_00_09 or core_orchestration'`

Expected: ten skills discovered in repository, CLI, and VS Code packages; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/skills .github/skills packages tests/test_skills.py
git commit -m "feat: add core Copilot workflow skills"
```

---

### Task 12: Assurance and Domain Skills PROC-10–PROC-20

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-orm-query-optimization/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-performance-optimization-lifecycle/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-severity-based-code-review/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-documentation-gap-closure/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-accessible-ui-delivery/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-test-strategy-design/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-secure-code-assessment/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-deployment-safety-pipeline/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-reproducible-ml-lifecycle/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-authorized-scraping-pipeline/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-bounded-instruction-update/SKILL.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-orm-query-optimization/references/evidence.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-accessible-ui-delivery/references/checklist.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-secure-code-assessment/references/severity.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-deployment-safety-pipeline/references/rollout-rollback.md`
- Create: `/var/www/projetos/awesome-copilot-agents/src/skills/aca-authorized-scraping-pipeline/references/safety.md`
- Modify: `/var/www/projetos/awesome-copilot-agents/tests/test_skills.py`
- Modify: `/var/www/projetos/awesome-copilot-agents/tests/test_safety.py`

**Interfaces:**
- Consumes: procedures PROC-10–20 and safely retained repeated source procedures.
- Produces: remaining 11 skills and exact 21/21 package coverage.

- [ ] **Step 1: Extend failing discovery, safety, and evidence tests**

Assert all 21 exact names exist once in every package. Pin ORM/performance before-and-after evidence, review severities and PASS/BLOCK, docs artifact/changelog output, accessibility/visual fallback, risk-layered tests, read-only security assessment, deployment rollout/rollback gates, reproducible ML metadata, authorized acquisition refusal, and generated-block-only instruction mutation.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_skills.py tests/test_safety.py -q`

Expected: FAIL because PROC-10–20 are absent.

- [ ] **Step 3: Author the 11 entry skills and five resources**

Keep entry files concise and move long checklists/examples into the named references. `aca-authorized-scraping-pipeline` contains no bypass instructions and makes authorization a prerequisite. `aca-bounded-instruction-update` limits edits to a generated block, requires a preview, and obtains AP-X.

- [ ] **Step 4: Generate and test**

Run: `.venv/bin/python scripts/generate.py --release && .venv/bin/python -m pytest tests/test_skills.py tests/test_safety.py -q`

Expected: exactly 21 skills in every package; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/skills .github/skills packages tests/test_skills.py tests/test_safety.py
git commit -m "feat: add assurance and domain Copilot skills"
```

---

### Task 13: Exact Source Provenance and Coverage Validation

**Files:**
- Verify unchanged: `/var/www/projetos/awesome-copilot-agents/provenance/source-baseline.json`
- Verify unchanged: `/var/www/projetos/awesome-copilot-agents/provenance/agents.csv`
- Create: 33 files under `/var/www/projetos/awesome-copilot-agents/provenance/lineage/`, one exact canonical ID per YAML filename
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/provenance.schema.json`
- Modify: `/var/www/projetos/awesome-copilot-agents/aca_tools/provenance.py`
- Modify: `/var/www/projetos/awesome-copilot-agents/scripts/verify_upstream.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_provenance.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/fixtures/provenance/root-claude-approval.yaml`

**Interfaces:**
- Consumes: immutable baseline/identity authority, source repository at exact commit, 33 canonical profiles, 21 skills, contracts, and approved decision ID.
- Produces: `load_lineage(root: Path, agent_id: str) -> Lineage`; `validate_partitions(lineage: Lineage, line_count: int) -> None`; extended `verify_upstream(source_root: Path, baseline: SourceBaseline) -> VerificationReport` covering lineages/destinations.

- [ ] **Step 1: Write failing partition and discriminated-schema tests**

```python
def test_source_ranges_partition_every_line_once(lineage, baseline):
    derived = [d.source_range for d in lineage.dispositions if d.kind == "source-derived"]
    assert flatten(derived) == list(range(1, baseline.line_count + 1))


def test_vue_additive_behavior_has_null_range_and_authority(vue_lineage):
    additive = [d for d in vue_lineage.dispositions if d.kind == "additive"]
    assert additive
    assert {d.source_range for d in additive} == {None}
    assert {d.design_authority for d in additive} == {"VUE-03-SEMANTIC-REPAIR"}


def test_additive_status_is_rejected_on_integer_range(validate_lineage):
    with pytest.raises(ValidationError, match="additive requires source_range: null"):
        validate_lineage({"kind": "additive", "source_range": {"start_line": 1, "end_line": 2}})
```

```python
def test_root_claude_approval_lineage_is_pinned(baseline):
    approval = baseline.approval_lineage
    assert approval.path == "CLAUDE.md"
    assert approval.sha256 == "c2cc9e33425eedfe433d0699d0085e4548897fd33a33ca1cdf51b9b67990eeed"
    assert approval.ranges == ((101, 106), (189, 189))
```

Also assert PY-09 source lines 1499–1534 are `omitted-for-safety` when those lines exist in the fixed source baseline; the source/license SHA-256 values match; `agents.csv` retains every original source path and declared frontmatter name, including malformed/colliding identities; and package-manifest attribution equals the ledger.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_provenance.py -q`

Expected: FAIL because detailed lineage artifacts, discriminated lineage schema, and partition/destination validation do not exist.

- [ ] **Step 3: Re-verify the immutable authority before authoring lineages**

Run `.venv/bin/python scripts/verify_upstream.py --source-root /var/www/projetos/awesome-claude-agents --baseline-only` and compare `provenance/source-baseline.json` plus `provenance/agents.csv` to the Task 1 commit. Stop on any source, license, approval, or identity-ledger drift; Task 13 may extend validators but must not regenerate or rewrite the authority it is about to disposition.

- [ ] **Step 4: Author all 33 complete line partitions**

Every source line belongs to exactly one `source-derived` disposition targeting a profile, skill, resource, contract, or omission record. Additive entries never consume source lines. `agents.csv` maps source path, original declared name, canonical ID, contract, identity disposition, and lineage file. `vue-state-manager.yaml` partitions duplicated lines 1–33 to the consolidated Vue component destination and separately records additive state behavior with null range and `VUE-03-SEMANTIC-REPAIR`. PY-09 records exact unsafe ranges, rationale, and safe replacement destination.

- [ ] **Step 5: Validate upstream, partitions, and destinations**

Run: `.venv/bin/python scripts/verify_upstream.py --source-root /var/www/projetos/awesome-claude-agents && .venv/bin/python -m pytest tests/test_provenance.py -q`

Expected: 33/33 source hashes match; root `CLAUDE.md` approval hash/ranges match; original filename/name defects remain traceable; line disposition is 100%; every destination exists; tests PASS.

- [ ] **Step 6: Commit**

```bash
git add provenance src/schemas/provenance.schema.json aca_tools/provenance.py scripts/verify_upstream.py tests/fixtures/provenance tests/test_provenance.py
git commit -m "feat: add exact upstream provenance ledger"
```

---

### Task 14: Collision-Safe Repository, CLI, and VS Code Installation

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/install.py`
- Modify: `/var/www/projetos/awesome-copilot-agents/aca_tools/cli.py`
- Create: `/var/www/projetos/awesome-copilot-agents/scripts/install.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_install.py`
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/install-state.schema.json`

**Interfaces:**
- Consumes: generated package roots and sorted digest manifests.
- Produces: `plan_install(package_root: Path, target_root: Path) -> InstallPlan`; `apply_install(plan: InstallPlan, backup_root: Path | None) -> InstallReport`; `plan_uninstall(manifest: Path, target_root: Path) -> UninstallPlan`; versioned persistent installed-state manifests; CLI `install`, `upgrade`, and `uninstall` commands.

- [ ] **Step 1: Write failing fresh/idempotent/collision/upgrade/uninstall tests**

Pin all required scenarios across two package versions: fresh repository install; idempotent reinstall; generated-file replacement and stale generated-file removal; preexisting non-generated collision refusal; user-modified generated file refusal; digest-matching uninstall; digest-mismatching uninstall refusal; target path containing spaces; path traversal in package or installed-state manifest; no write outside target root; failed upgrade after one replacement restores all files and prior state. CLI user destinations are `.copilot/agents` and `.copilot/skills`; optional skill-only destination `.agents/skills`; VS Code package remains an import source and requires an explicit destination.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_install.py -q`

Expected: FAIL because installer interfaces do not exist.

- [ ] **Step 3: Implement pure planning before mutation**

```python
@dataclass(frozen=True, slots=True)
class InstallAction:
    source: Path | None
    destination: Path
    old_sha256: str | None
    new_sha256: str | None
    disposition: Literal[
        "create", "unchanged", "replace-generated", "remove-generated", "conflict"
    ]


@dataclass(frozen=True, slots=True)
class InstallPlan:
    state_path: Path
    actions: tuple[InstallAction, ...]
    conflicts: tuple[Path, ...]
```

Resolve every source and destination and assert it is contained by its resolved package or target root. Persist schema-versioned ownership state at `.github/.awesome-copilot-agents-install.json` for repository installs, `.copilot/.awesome-copilot-agents-install.json` for CLI installs, `.agents/.awesome-copilot-agents-install.json` for optional skill-only installs, and `.awesome-copilot-agents-install.json` under the explicitly selected VS Code import target. State records `package_id`, the installed package-manifest digest, and sorted `{path, installed_sha256}` entries. An upgrade compares current bytes to the *previous installed-state* digests before planning replacements/removals; the new package manifest alone is never treated as prior ownership proof. Print the plan before mutation. Any collision exits nonzero without writes. `--backup-dir` is required for an upgrade that replaces or removes files.

- [ ] **Step 4: Implement transactional apply, state replacement, and digest-safe uninstall**

Stage new bytes on the target filesystem. Before the first mutation, copy every replace/remove target plus the prior state file to the backup directory. Apply actions in deterministic order, write the new state to a temporary sibling, and atomically replace state only after all file actions succeed. On any exception, remove newly created files, restore replaced/removed files and old state in reverse order, and report the failed action. Uninstall locates the package-specific state path, deletes only files whose current SHA-256 equals `installed_sha256`, removes only empty package-owned directories, and removes state last; any digest mismatch leaves all files and state untouched for explicit resolution.

- [ ] **Step 5: Run focused tests and an actual temporary install smoke**

Run:

```bash
.venv/bin/python -m pytest tests/test_install.py -q
root="$(mktemp -d '/tmp/aca install.XXXXXX')"
.venv/bin/python scripts/install.py install repository --target "$root/repo with spaces"
.venv/bin/python scripts/install.py install repository --target "$root/repo with spaces"
.venv/bin/python scripts/install.py uninstall repository --target "$root/repo with spaces"
```

Expected: tests PASS; first install creates owned files, second is unchanged, uninstall removes only matching owned files.

- [ ] **Step 6: Commit**

```bash
git add aca_tools/install.py aca_tools/cli.py scripts/install.py src/schemas/install-state.schema.json tests/test_install.py
git commit -m "feat: add collision-safe Copilot package installer"
```

---

### Task 15: Bilingual Documentation, CI, Surface Smoke Harness, and Release Gate

**Files:**
- Create: `/var/www/projetos/awesome-copilot-agents/README.md`
- Create: `/var/www/projetos/awesome-copilot-agents/README.pt-BR.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/install-repository.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/install-cli.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/install-vscode.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/agents.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/skills.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/compatibility.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/en/troubleshooting.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/install-repository.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/install-cli.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/install-vscode.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/agents.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/skills.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/compatibility.md`
- Create: `/var/www/projetos/awesome-copilot-agents/docs/pt-BR/troubleshooting.md`
- Create: `/var/www/projetos/awesome-copilot-agents/CONTRIBUTING.md`
- Create: `/var/www/projetos/awesome-copilot-agents/LICENSE`
- Create: `/var/www/projetos/awesome-copilot-agents/NOTICE`
- Create: `/var/www/projetos/awesome-copilot-agents/CHANGELOG.md`
- Create: `/var/www/projetos/awesome-copilot-agents/aca_tools/release.py`
- Create: `/var/www/projetos/awesome-copilot-agents/src/schemas/smoke-evidence.schema.json`
- Create: `/var/www/projetos/awesome-copilot-agents/smoke/fixtures/ide.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/smoke/fixtures/cli.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/smoke/fixtures/cloud.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/smoke/fixtures/installation.yaml`
- Create: `/var/www/projetos/awesome-copilot-agents/smoke/evidence/README.md`
- Create: `/var/www/projetos/awesome-copilot-agents/scripts/validate.py`
- Create: `/var/www/projetos/awesome-copilot-agents/scripts/smoke.py`
- Create: `/var/www/projetos/awesome-copilot-agents/.github/workflows/validate.yml`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_docs.py`
- Create: `/var/www/projetos/awesome-copilot-agents/tests/test_release.py`

**Interfaces:**
- Consumes: complete canonical/generated trees, installer, routing fixtures, provenance, package manifests.
- Produces: reader-facing bilingual project, `aca_tools.release.validate_release(root: Path) -> CoverageReport`, structured smoke evidence, CI release gate, version `0.1.0` without unsupported stability claims.

- [ ] **Step 1: Write failing documentation and release tests**

Assert English/pt-BR heading and internal-link parity; identical IDs, commands, paths, schema names, and official URLs; 33-agent and 21-skill catalogs; repository/CLI/VS Code install-update-uninstall; explicit-selection guidance; permissions; optional MCP/browser; cloud separate sessions; troubleshooting; provenance/license; tested versions. Release coverage reports identity 33/33, canonical consistency 33/33, source-line disposition 100%, root approval lineage 100%, contracts 33/33, procedures 21/21, routing/tool/approval 33/33, safety 100%, attribution 33/33, package inventory 100%, and a surface smoke matrix. A `not-exercised`, failed, stale-digest, wrong-version, or missing required surface record must fail release validation.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_docs.py tests/test_release.py -q`

Expected: FAIL because docs, smoke schema, and release validator are absent.

- [ ] **Step 3: Write English normative docs and semantically equivalent pt-BR docs**

Document only official supported paths and surface capabilities from spec §4/§12. VS Code user destinations are labeled version-sensitive and tied to the tested release. GitHub.com has repository installation only and no subagents. Include exact collision/backup/uninstall semantics and safety boundaries. `NOTICE` records the upstream repository, commit, MIT attribution, and adaptation statement. `CHANGELOG.md` opens version `0.1.0` as an initial compatibility release, not a stability guarantee.

- [ ] **Step 4: Implement one release validator**

`aca_tools.release.validate_release(root: Path) -> CoverageReport` runs catalog/schema, generation `--release --check`, profile character/banned-token, contract fixtures, routing fixtures, provenance including root approval lineage, package attribution/digests, installer-state schema, docs parity/link, safety, coverage, and retained surface evidence checks. It succeeds only when every §13.3 VS Code, CLI, GitHub.com, and installation criterion has a `passed` manual or automated record for the current package digest and pinned platform version. `scripts/validate.py --development` reports unavailable surfaces as `not-exercised` without claiming release eligibility; `scripts/validate.py --release` calls the strict validator and exits nonzero for `not-exercised`, failed, stale, or missing evidence. Both modes emit stable JSON plus a human table; no environment variable or flag converts incomplete evidence to a release pass.

- [ ] **Step 5: Implement and exercise the smoke harness**

`smoke.py` records `{surface, platform_version, package_digest, selected_agent, fixture, observed_contract_id, observed_status, artifacts, disposition, observed_at}` and validates the record before saving; agent/contract fields are nullable only for the installation fixture. Run actual available checks for `project-analyst`, `tech-lead-orchestrator`, `vue-state-manager`, and `python-security-expert`, plus the Task 14 installation matrix. CLI checks use `/agent` and `--agent` only when the installed CLI advertises them. IDE and cloud observations remain manual evidence unless those surfaces are actually available. A missing browser/MCP fixture must return the explicit fallback and no fabricated artifact. `not-exercised` remains truthful development evidence but never satisfies a release gate.

- [ ] **Step 6: Add CI and run full verification**

CI uses Python 3.11 and 3.12, installs pinned dependencies, runs generation drift check, full pytest, upstream provenance verification against a checkout pinned to the exact commit, and development validation on every change. A separate tag/manual release job runs strict `--release` validation against retained evidence whose package digest matches the candidate. Locally run:

```bash
.venv/bin/python scripts/generate.py --release
.venv/bin/python scripts/generate.py --release --check
.venv/bin/python scripts/validate.py --development
.venv/bin/python -m pytest -q
.venv/bin/python scripts/smoke.py --available-surfaces
.venv/bin/python scripts/validate.py --release
```

Expected: structural/routing/generation/install/docs/safety/provenance checks PASS; every exercised real surface has retained evidence. If any required surface is unavailable, development validation reports `not-exercised`, strict release validation fails, and no release/tag is claimed until qualifying evidence is retained.

- [ ] **Step 7: Commit**

```bash
git add README.md README.pt-BR.md docs CONTRIBUTING.md LICENSE NOTICE CHANGELOG.md aca_tools/release.py src/schemas/smoke-evidence.schema.json smoke scripts/validate.py scripts/smoke.py .github/workflows tests/test_docs.py tests/test_release.py
git commit -m "docs: add bilingual release and compatibility validation"
```

---

## Final Whole-Project Verification

- [ ] Run `.venv/bin/python scripts/generate.py --release --check`; expected: zero drift and `complete: true` in every generated manifest.
- [ ] Run `.venv/bin/python scripts/validate.py --release`; expected: every non-surface coverage dimension is complete and all VS Code, CLI, GitHub.com, and installation smoke gates have current-digest `passed` evidence; `failed` or `not-exercised` blocks completion.
- [ ] Run `.venv/bin/python -m pytest -q`; expected: zero failures.
- [ ] Run `.venv/bin/python scripts/verify_upstream.py --source-root /var/www/projetos/awesome-claude-agents`; expected: commit/blob/license and 33/33 line partitions verified.
- [ ] Run the temporary-path install smoke from Task 14; expected: fresh install, unchanged reinstall, and digest-safe uninstall.
- [ ] Run `.venv/bin/python scripts/smoke.py --available-surfaces`; expected: retained evidence for every surface actually available, no fabricated pass for unavailable surfaces.
- [ ] Ask a fresh reviewer to compare all 12 spec acceptance criteria against files, generated distributions, test output, validation JSON, and smoke evidence; fix every P0/P1 before delivery.
- [ ] Confirm `git status --short` is clean and record the final commit range and exercised versions in the delivery report.
