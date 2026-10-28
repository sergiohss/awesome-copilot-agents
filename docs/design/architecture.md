# Awesome Copilot Agents — Architecture and Conversion Specification

**Status:** Approved design
**Decision date:** 2026-10-28
**Target project:** `/var/www/projetos/awesome-copilot-agents`
**Source baseline:** `https://github.com/vijaythecoder/awesome-claude-agents.git` at `2050f3c60fcfea497f7b6b3ec6566cc316367a7e`

## 1. Purpose and problem statement

The source repository is a useful Claude-oriented prompt library, but it is not a portable GitHub Copilot distribution. Its 33 files contain only 32 distinct declared names, seven filename/name mismatches, a duplicated Vue identity, malformed frontmatter, vendor-specific tools and model settings, dangling delegation targets, inconsistent output contracts, and profiles large enough to exceed Copilot's 30,000-character profile limit. The README's 24-agent claim is stale; the file inventory is authoritative.

The target is a separate, generated, MIT-licensed project for all three requested Copilot surfaces: VS Code/IDE, GitHub.com coding agent, and Copilot CLI. It preserves exactly 33 lean public identities while moving reusable procedures and large reference material into cross-surface Agent Skills and resources. A canonical manifest and provenance ledger are the sole design-time authority; checked-in distributions are deterministic generated outputs, not separately maintained forks.

### 1.1 Source-audit conclusions

- The source has three orchestrators, four core agents, four universal agents, framework specialists, and Python specialists.
- Five imported Python identities require canonical `python-*` prefixes. `frontend-developer` has malformed frontmatter. Several profiles omit tools, which would grant all available tools on Copilot rather than least privilege.
- Claude tool names, `model: opus`, `@agent-*`, direct “ping/delegate” language, `sandbox:/mnt/...` artifacts, and mandatory WebFetch/Context7 assumptions are not portable as written.
- The source's maximum-two-agent rule is policy, not a Copilot engine limit. GitHub.com has no subagent runtime; VS Code and CLI do.
- Six dangling identities are replaced with existing canonical agents; no 34th profile is introduced.
- Large manuals and repeated procedures belong in skills/resources. Every source line still requires an explicit provenance disposition.

## 2. Goals and non-goals

### 2.1 Goals

1. Publish exactly 33 truthful, selectable public agents with stable canonical IDs.
2. Support repository installation on all requested surfaces and user installation only for CLI and VS Code where officially supported.
3. Preserve source behavior, required outputs, attribution, and lineage unless explicitly corrected, consolidated, translated, made non-portable, or omitted for safety.
4. Use exact, least-privilege portable tool aliases and explicit approval/risk policies.
5. Provide deterministic routing, typed Handoff v1 results, and honest surface fallbacks.
6. Keep generated profiles below the project hard ceiling of 12,000 Unicode scalar values, warn above 8,000, and remain safely below Copilot's documented 30,000-character platform limit; load detailed procedures progressively through exactly 21 skills, PROC-00 through PROC-20.
7. Generate English prompts and English plus pt-BR installation/reader documentation.
8. Make source coverage, generated consistency, safety, and release readiness mechanically auditable.

### 2.2 Non-goals

- Organization or enterprise packaging, installation, or centrally inherited skills.
- Personal GitHub.com cloud-agent installation; cloud coverage is repository-scoped.
- Reproducing Claude-specific invocation syntax, tool names, model selection, or runtime behavior.
- Depending on prompt files, handoff buttons, generic cloud web access, MCP credentials, or optional frontmatter for portability.
- Claiming deterministic automatic model inference among 33 profiles.
- Bundling MCP configuration or credentials; MCP/browser capability remains optional and surface-specific.
- Creating a general agent runtime, bypassing platform permission controls, or granting skills silent command preapproval.
- An implementation task plan. This document defines architecture and acceptance only.

## 3. Approved decisions and invariants

- The catalog contains exactly 33 public identities listed in §7.
- The canonical manifest and provenance ledger are the only editable semantic authorities; all profiles, skills, instructions, schemas, fixtures, and packages derive from them.
- Portable profile frontmatter is exactly:

```yaml
---
name: <canonical-id>
description: <routing description>
tools: [<explicit static portable aliases>]
---
```

- Portable profiles do not depend on `target`, `model`, `user-invocable`, `disable-model-invocation`, `infer`, `metadata`, `mcp-servers`, `handoffs`, `argument-hint`, or unresolved schema fields.
- Every profile contains directly injected evidence/non-fabrication, role boundary, static tool policy, approval policy, surface fallback, Handoff v1, typed-contract, next-agent, and attribution clauses. Generated profiles contain no unresolved `INS-*`, `REF-*`, `SKL-*`, or `PROC-*` token.
- The user/session model is inherited. Automatic inference is best effort; explicit user/coordinator selection is authoritative.
- Specialists precede universal fallbacks. Coordinators permit at most two concurrent agents in IDE/CLI. Cloud stages are sequential, separately selected sessions.
- Prompts and skill content are English. README and installation documentation have semantically equivalent English and pt-BR editions.
- MIT SPDX, license text, upstream attribution, commit, exact paths/ranges, and hashes are preserved.

## 4. Official platform constraints

The following are design constraints, not assumptions:

- Repository custom agents use `.github/agents/`; profiles are Markdown with YAML frontmatter and have a 30,000-character prompt limit. Tool aliases are case-insensitive and unknown names are ignored: [custom-agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration).
- Agent Skills are supported across VS Code agent mode, GitHub.com coding agent, and CLI; each skill is a directory with `SKILL.md`: [Agent Skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills), [CLI skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills), and [cloud skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).
- GitHub.com does not support subagents or prompt files. VS Code and CLI support subagents through different mechanisms: [customization support matrix](https://docs.github.com/en/copilot/reference/customization-cheat-sheet), [IDE subagents](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents), and [CLI delegation](https://docs.github.com/en/copilot/concepts/agent-capabilities/choosing-and-delegating-agent-work/delegating-and-parallelizing-work-with-agents).
- VS Code Local handoff metadata is surface-specific; GitHub.com ignores it. Portable releases therefore express handoffs in the response contract: [VS Code agent file reference](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference#handoff-fields) and [GitHub configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration).
- CLI supports `/agent`, `--agent`, and inferred custom-agent selection. User agents live in `~/.copilot/agents/`: [CLI custom-agent reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference#custom-agent-locations).
- Repository and path-specific instructions are supported, but ordering/precedence differs by surface. Generated instruction files must therefore be individually non-conflicting: [custom-instruction support](https://docs.github.com/en/copilot/reference/custom-instructions-support) and [CLI custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions).
- Tool availability and execution approval are separate. CLI allow/deny controls and VS Code terminal confirmation remain authoritative: [CLI tool permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools) and [IDE agent mode](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-agent-mode).
- Cloud work occurs on an agent branch and produces a draft PR for review; configured MCP tools may run autonomously, so credentials and external effects require explicit policy gates: [cloud risk mitigations](https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations) and [cloud MCP](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers).
- MCP configuration is surface-specific and is not generated by this project: [VS Code MCP](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/customize-copilot/extend-copilot-with-tools-and-context/extend-copilot-chat-with-mcp), [cloud MCP](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers), and [CLI MCP](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers).

Documentation was accessed on 2026-10-28. Version-sensitive VS Code user-profile destinations must be pinned and tested against the release documented by the project; the architecture must not invent a cross-version location.

## 5. Canonical architecture and layout

### 5.1 Design-time source tree

```text
src/
  catalog/agents.yaml                 # 33 identities, routing, tools, approvals, contracts
  catalog/procedures.yaml             # PROC-00..20 and exact skill names
  catalog/contracts.yaml              # primary contract registry
  catalog/instructions.yaml           # repository/path applicability
  schemas/                             # manifest, provenance, Handoff v1, typed result schemas
  profiles/                            # concise agent-specific English source bodies
  skills/<aca-skill>/                  # canonical SKILL.md and references/resources
  fragments/
    ins-core.md
    approval-orchestrated-complex.md
    approval-bounded-request-is-authorization.md
    approval-explicit-before-external-side-effect.md
    approval-review-only.md
    handoff-v1.md
    surface-fallback.md
  instructions/                       # canonical repository/path instruction bodies
  routing-fixtures/                    # positive, exclusion, precedence, and surface cases
provenance/
  agents.csv                          # one authoritative row per source agent
  lineage/<canonical-id>.yaml         # exact source ranges and destinations
  source-baseline.json                # upstream commit, file/license hashes
scripts/                               # deterministic generator and validators
docs/en/                               # English reader/install documentation
docs/pt-BR/                            # equivalent pt-BR reader/install documentation
```

Fragments are injected build inputs, never runtime references. Agent-specific bodies may refer to canonical skill names in natural language, but a generated profile must remain useful when a skill is not loaded.

### 5.2 Generated outputs

```text
.github/agents/*.agent.md
.github/skills/<aca-skill>/SKILL.md
.github/skills/<aca-skill>/references/**
.github/copilot-instructions.md
.github/instructions/**/*.instructions.md

packages/repository/portable/.github/agents/*.agent.md
packages/repository/portable/.github/skills/**
packages/repository/portable/.github/copilot-instructions.md
packages/repository/portable/.github/instructions/**/*.instructions.md

packages/user/cli/.copilot/agents/*.agent.md
packages/user/cli/.copilot/skills/**

packages/user/vscode/agents/*.agent.md
packages/user/vscode/skills/**
```

Path-specific instructions are emitted only when applicability is declared. Repository output and `packages/repository/portable` must be byte-equivalent after accounting only for their package root. `~/.agents/skills` is an optional CLI install destination, not another generated package. No cloud-personal, organization, or enterprise package exists.

### 5.3 Generation contract

Generation is deterministic for identical canonical inputs: stable UTF-8/NFC/LF output, stable ordering, no timestamps, absolute paths, environment-derived content, secrets, or network-fetched text. It validates inputs before writing and stages a complete output set before replacement. A failed generation leaves the previous set intact. Agent profiles contain no generator comments; generation metadata and detailed lineage remain in provenance. Other generated artifacts may carry a concise notice only when their format supports it.

The generator counts Unicode scalar values across the exact final profile, including frontmatter, body, line breaks, and comments. It warns above 8,000 scalar values and rejects profiles above the project hard ceiling of 12,000; Copilot's documented platform ceiling is 30,000 characters. Package manifests enumerate every output and digest so stale, missing, duplicate, or hand-edited generated files fail consistency validation.

## 6. Tools, approvals, surfaces, and failure behavior

### 6.1 Static tool policies

| Policy | Exact tools | Purpose |
|---|---|---|
| T-R | `read`, `search` | Read-only investigation |
| T-RX | `read`, `search`, `execute` | Investigation plus evidence-producing commands |
| T-O | `read`, `search`, `agent` | Coordination; cloud returns a Route Plan instead of calling `agent` |
| T-E | `read`, `search`, `edit` | Bounded generated-block configuration mutation |
| T-W | `read`, `search`, `edit`, `execute` | Repository-local implementation/specification work |

Optional browser/MCP tools never alter a profile's static list. An unavailable alias triggers the surface fallback; it does not justify broadening tools.

### 6.2 Approval policies

| Policy | Contract |
|---|---|
| AP-OC | `orchestrated-complex`: research findings and assumptions require approve/revise/stop before execution planning |
| AP-B | `bounded-request-is-authorization`: a direct bounded request authorizes repository-local work within that scope |
| AP-X | `explicit-before-external-side-effect`: approval precedes deployment, destructive action, instruction/catalog mutation, credential-bearing MCP setup, or scraping acquisition |
| AP-R | `review-only`: analysis only; remediation requires a separate assignment |

A row's `risk_gate` is additive and action-specific. Runtime platform approvals still apply even when a prompt policy authorizes work.

### 6.3 Surface codes

- **P — Portable:** directly select the profile; inference is best effort.
- **H — Handoff/orchestration:** VS Code may use `agent`/`runSubagent`; CLI may delegate/communicate subject to the two-agent policy; cloud returns a Route Plan or recommendation for a new separately selected session.
- **D — Documentation:** installed/local/repository documentation first; optional official web/MCP capability second. No generic cloud `web` assumption.
- **V — Visual/browser:** optional configured browser/MCP capability; absence is reported, and artifacts remain repository/PR-visible.
- **C — Configuration:** preview a generated-block diff and obtain AP-X approval before mutation.

### 6.4 Errors and fallbacks

- Missing optional web/MCP/browser capability: use local evidence, mark unavailable evidence explicitly, and return `blocked` only if the requested result cannot be truthful without it.
- Missing `agent` capability: return `needs-approval` or `completed` Route Plan as appropriate; never impersonate the next agent.
- Ambiguous routing: report candidates and exclusions; request explicit selection rather than fabricate inference certainty.
- Unsupported or unknown frontmatter: fail generation; never silently emit it.
- Missing skill/resource: profile continues with its core contract, reports the missing package artifact, and does not invent detailed procedure content.
- Permission denial or external-side-effect gate: preserve work, identify the denied action and prerequisite, and return `needs-approval`; do not weaken the gate.
- Contract validation failure: no successful handoff is emitted. Generation/release fails with the profile and field path.
- Destructive migration/load test/deployment/scraping without its row risk gate: stop before the action and return the required prerequisite.
- Cloud recommendation: always says to start a separately selected session; it never claims the current agent changed roles.

## 7. Canonical 33-agent catalog

Each row is normative. “Manual” means explicit selection is required for the risky or configuration role; “no” still permits explicit selection and does not promise deterministic inference.

| ID | Primary contract | Procedures | Surface; tools; approval/risk | Primary routing and result contract |
|---|---|---|---|---|
| `tech-lead-orchestrator` | `route-plan-v1` | 00,03,04,05 | H; T-O; AP-OC | Complex multi-step/architecture; excludes bounded specialist work. Returns exact assignments, dependencies/concurrency, whitelist, approval status, handoffs. Cloud manual between stages. |
| `project-analyst` | `stack-analysis-v1` | 01,02 | P; T-RX; AP-R | New/unfamiliar stack; excludes deep audit. Returns stack, architecture, confidence, findings, contradictions, unknowns, recommendations. |
| `team-configurator` | `team-configuration-v1` | 01,02,05,20 | H+C; T-E; AP-X/instruction mutation; Manual | Explicit setup/refresh after stack evidence; generated block only. Returns stack and selected-agent table. |
| `code-archaeologist` | `codebase-assessment-v1` | 01,02,07,16 | H; T-RX; AP-R | Legacy/complex deep audit; deeper than project analyst. Retains all 11 assessment sections. |
| `code-reviewer` | `code-review-v1` | 12,16 | H; T-RX; AP-R | Completed change/PR; excludes implementation. Returns grades, severities, positives, file:line findings, checklist, PASS/BLOCK. |
| `documentation-specialist` | `documentation-changelog-v1` | 13 | H; T-W; AP-B | Reader-facing docs; API authority remains `api-architect`. Returns artifacts and one-line summaries. |
| `performance-optimizer` | `performance-report-v1` | 11 | H; T-W; AP-B/destructive load test | Cross-stack performance; narrower ORM/Python specialists win. Returns baseline, bottleneck, before/after/delta, recommendations. |
| `api-architect` | `api-design-report-v1` | 08 | D; T-W; AP-B | Technology-independent API contract before implementation. OpenAPI/GraphQL artifact, decisions, questions, validation, implementer steps. |
| `backend-developer` | `backend-implementation-v1` | 05,07,09 | H+D; T-W; AP-B | Server fallback only when no exact framework. Returns stack, files, endpoints, design, migrations/security, tests, performance. |
| `frontend-developer` | `frontend-implementation-v1` | 05,07,09,14 | H+V; T-W; AP-B | UI fallback only when no React/Vue specialist. Returns framework, components, responsiveness, accessibility, files, next steps. |
| `tailwind-css-expert` | `component-delivery-v1` | 06,14 | D+V; T-W; AP-B | Tailwind utility/theme work. Returns files, repository visual artifact, checklist, next steps. |
| `laravel-backend-expert` | `laravel-implementation-v1` | 06,07,09 | H+D; T-W; AP-B | Laravel application logic; excludes isolated Eloquent/contract work. Returns architecture, files, DB/UI integration, dependencies/tests/docs. |
| `laravel-eloquent-expert` | `eloquent-work-summary-v1` | 06,07,09,10 | D; T-W; AP-B/destructive migration | Laravel persistence/query bottlenecks. Returns models/migrations, decisions, evidence, next steps. |
| `django-backend-expert` | `django-backend-implementation-v1` | 06,07,09 | H+D; T-W; AP-B | Focused Django backend; API/ORM/full-stack excluded. Returns components, features, integration, next work, files. |
| `django-api-developer` | `django-api-implementation-v1` | 06,07,08,09 | H+D; T-W; AP-B | DRF/GraphQL exact owner. Returns endpoints, auth, serializers, docs/tests, integration/performance, files. |
| `django-orm-expert` | `django-orm-optimization-v1` | 06,07,10,11 | H+D; T-W; AP-B/destructive migration | Django query/schema performance. Returns metrics, DB/code changes, impact, monitoring, recommendations, files. |
| `django-expert` | `django-fullstack-implementation-v1` | 06,07,09 | H+D; T-W; AP-B | Cross-cutting Django templates/admin/DRF/Celery integrator. Returns apps/models/views, architecture, UI/admin, APIs/jobs, files. |
| `rails-backend-expert` | `rails-backend-implementation-v1` | 06,07,09 | H+D; T-W; AP-B | Rails application logic; excludes API/ActiveRecord-only. Returns components, features, integrations, gems, next steps, files. |
| `rails-api-developer` | `rails-api-implementation-v1` | 06,07,08,09 | H+D; T-W; AP-B | Rails REST/GraphQL/auth. Returns endpoints/versioning, security, serialization/errors, docs/tests, integration, files. |
| `rails-activerecord-expert` | `rails-activerecord-optimization-v1` | 06,07,10,11 | H+D; T-W; AP-B/destructive migration | ActiveRecord query/schema exact owner. Returns metrics, DB/AR changes, impact, recommendations, files. |
| `react-component-architect` | `react-component-delivery-v1` | 06,07,09,14 | H+D+V; T-W; AP-B | React components/hooks/design systems; Next framework concerns excluded. Additive contract: boundaries, server/client choice, accessibility, tests/stories, performance, files. |
| `react-nextjs-expert` | `nextjs-implementation-v1` | 06,07,09,14 | H+D+V; T-W; AP-B | Next routing/rendering/cache/SEO/server actions. Returns rendering/router, features, performance, SEO, integration, files. |
| `vue-component-architect` | `vue-implementation-v1` | 06,07,09,14 | H+D+V; T-W; AP-B | Vue components/composables; Nuxt/state-only excluded. Returns components, patterns, performance, state/router impact, next steps. |
| `vue-nuxt-expert` | `nuxt-implementation-v1` | 06,07,09,14 | H+D+V; T-W; AP-B | Nuxt/Nitro/rendering/server/SEO exact owner. Returns architecture, features, performance, SEO, integrations, files. |
| `vue-state-manager` | `vue-state-delivery-v1` | 06,07 + approved repair | H+D; T-W; AP-B | Pinia/Vuex stores, persistence, SSR hydration, migration; ordinary components excluded. Additive contract covers stores/actions/getters, flow, persistence/hydration, migration, consumers, tests, files. |
| `python-expert` | `python-implementation-v1` | 06,07,09 | H+D; T-W; AP-B | Python language/runtime/general application; exact specialists win. Returns components, features, integration, dependencies, next steps, files. |
| `fastapi-expert` | `fastapi-implementation-v1` | 06,07,08,09 | H+D; T-W; AP-B | FastAPI/Pydantic/async exact owner. Returns APIs, schemas/auth, architecture, performance/security, OpenAPI, files. |
| `ml-data-expert` | `ml-data-implementation-v1` | 06,07,09,18 | H+D; T-W; AP-B/external model or data side effect | ML/data/training/serving. Returns problem/model/known metrics, pipeline, training, production, visualization, files. |
| `python-devops-cicd-expert` | `python-deployment-delivery-v1` | 07,09,17 | H; T-W; AP-X/deployment, credentials, destructive infrastructure; Manual | Python CI/CD, containers, IaC, rollout/rollback. Additive typed pipeline/deployment result; examples live in resources. |
| `python-performance-expert` | `python-performance-report-v1` | 11 | H; T-W; AP-B | Python runtime/concurrency/CPU/memory. Returns workload, profiler evidence, before/after, regression disposition. |
| `python-security-expert` | `python-security-assessment-v1` | 12,16 | H; T-RX; AP-R/credential-bearing scans | Python security assessment, not remediation. Returns scope, assets, threats, severity, evidence, controls, remediation, verification, disposition. |
| `python-testing-expert` | `python-testing-delivery-v1` | 15 | H; T-W; AP-B | Python strategy/infrastructure/flakiness/property/mutation; routine feature tests excluded. Returns risk map, layers, fixtures, files, commands/evidence, coverage/mutation, gaps. |
| `python-web-scraping-expert` | `python-acquisition-report-v1` | 19 | D+V; T-W; AP-X/authorization, credentials, acquisition; Manual | Only explicitly authorized acquisition. Returns authorization, source/API preference, robots/terms/rate controls, schema, validation, lineage; no bypass/evasion. |

Dangling source edges resolve as follows: `security-guardian` → `python-security-expert` for Python, otherwise `code-reviewer` with PROC-16; `refactoring-expert` → matching implementer; `testing-specialist` → `python-testing-expert` for Python, otherwise matching implementer; `accessibility-expert` → matching frontend agent with PROC-14; `laravel-api-architect` → `api-architect` then `laravel-backend-expert`; `database-architect` → matching ORM agent, otherwise `backend-developer`.

## 8. Canonical procedure/skill catalog

There is no parallel `SKL-*` namespace. Directory name, `SKILL.md` `name`, catalog value, package path, provenance, and fixtures must match exactly.

| Procedure | Exact skill name | Contract |
|---|---|---|
| PROC-00 | `aca-core-orchestration` | 33-agent catalog, Route Plan v1, Handoff v1, specialist precedence, two-agent policy, surface fallbacks, contracts, dangling-edge substitutions |
| PROC-01 | `aca-inventory-first-discovery` | Establish evidence-backed inventory before conclusions |
| PROC-02 | `aca-stack-detection-with-confidence` | Detect stack/architecture with confidence and unknowns |
| PROC-03 | `aca-deterministic-agent-routing` | Apply exact IDs, triggers, exclusions, precedence, dependencies |
| PROC-04 | `aca-human-approval-checkpoint` | Approve/revise/stop gate for complex orchestration |
| PROC-05 | `aca-specialist-first-selection` | Exact specialist before universal fallback |
| PROC-06 | `aca-version-aware-official-docs` | Installed/project version and local docs first; official capability second |
| PROC-07 | `aca-existing-convention-scan` | Reuse repository conventions before change |
| PROC-08 | `aca-contract-first-api-design` | Define and validate API contract before implementation |
| PROC-09 | `aca-structured-implementation-handoff` | Produce typed, artifact-aware implementation results |
| PROC-10 | `aca-orm-query-optimization` | Measure query/schema/index changes and migration risk |
| PROC-11 | `aca-performance-optimization-lifecycle` | Baseline, profile, change, compare, regressions |
| PROC-12 | `aca-severity-based-code-review` | Evidence-backed severity, disposition, PASS/BLOCK |
| PROC-13 | `aca-documentation-gap-closure` | Audience/gap analysis, accurate content, concise changelog |
| PROC-14 | `aca-accessible-ui-delivery` | Accessibility, responsive behavior, visual evidence |
| PROC-15 | `aca-test-strategy-design` | Risk-layered Python test strategy and evidence |
| PROC-16 | `aca-secure-code-assessment` | Scope, threat, evidence, control, remediation disposition |
| PROC-17 | `aca-deployment-safety-pipeline` | CI/CD, rollout, rollback, credential and infrastructure gates |
| PROC-18 | `aca-reproducible-ml-lifecycle` | Reproducible data/model/training/serving lifecycle |
| PROC-19 | `aca-authorized-scraping-pipeline` | Authorization, API preference, robots/terms/rate compliance, lineage |
| PROC-20 | `aca-bounded-instruction-update` | Generated-block-only instruction/catalog update with approved diff |

Skills must be concise entry points. Large examples, checklists, and version notes live under `references/**` and are loaded only when relevant. Skills must not use `allowed-tools` to bypass runtime confirmation.

## 9. Route Plan v1 and Handoff v1

### 9.1 Route Plan v1

A Route Plan is `route-plan-v1` inside Handoff v1. Its `result` contains:

- request summary and evidence-backed assumptions;
- ordered slices with exact canonical `agent_id`, objective, inputs, expected `contract_id`, dependencies, and artifact paths;
- concurrency groups, each containing no more than two agents;
- exact allowed-agent whitelist and explicit excluded alternatives;
- approval checkpoint state: `pending`, `approved`, `revised`, or `stopped`;
- surface execution mode: `ide-subagent`, `cli-delegation`, or `cloud-separate-session`;
- cloud session instructions and context payload for each next separately selected agent;
- completion/review gate and unresolved prerequisites.

The orchestrator does not implement slices. A bounded single-specialist request bypasses AP-OC and routes directly under that specialist's policy.

### 9.2 Handoff v1

```yaml
handoff_version: 1
contract_id: <row-primary-contract-id>
status: completed | blocked | needs-approval
summary: <short human-readable summary>
artifact_paths: []
routing:
  recommended_next_agent: <canonical-id-or-null>
  reason: <reason-or-null>
  prerequisites: []
result: {}
```

Every profile names exactly one primary contract. `result` validates against that contract's schema; reusable broad schemas may only be JSON Schema `$ref` bases. Source-required fields remain first-class fields under `result` and are never flattened into `summary`. Additive contracts are labeled as such in provenance. Artifact paths are repository-relative or PR-visible. A recommendation cannot name an identity outside the 33-row catalog.

## 10. Conversion, safety, and semantic repair

### 10.1 Conversion rules

1. Inventory by source file, not README count or declared name.
2. Resolve each source row to its exact canonical ID and contract before content conversion.
3. Translate French PY-01–04 content to English without removing required fields.
4. Extract reusable procedure text into its canonical PROC skill and large/detailed examples into skill resources. Keep role-specific scope, routing, approval, fallback, and result requirements in the profile.
5. Convert tools only to the row's one static T-policy. Omitted or contradictory source tools never become inherited-all access.
6. Remove vendor-specific model settings; inherit the user/session model.
7. Replace fixed “latest” claims with detected project-version guidance and official compatible documentation.
8. Replace WebFetch/Context7 requirements with local-first PROC-06 and optional configured official-doc capability.
9. Replace `@agent-*`, ping, and delegation syntax with exact IDE/CLI selection or cloud separate-session recommendations.
10. Replace `sandbox:/mnt/...` with repository-relative/PR-visible artifacts.
11. Retain every source-required output field in the typed `result`; add a contract only where the source had none and mark it additive.
12. Normalize identity/frontmatter defects, but retain original filename/name in provenance.
13. Apply dangling-edge substitutions exactly as §7 states.
14. Keep generated profiles lean, self-contained, attributable, and below the character cap.

### 10.2 Unsupported-behavior dispositions

| Code | Required disposition |
|---|---|
| X-A | Claude handles/direct delegation → exact IDE/CLI selection or cloud recommendation |
| X-G | Cloud subagent graph → Route Plan plus separate selected cloud sessions |
| X-2 | Engine-enforced two-agent maximum → coordinator policy; cloud sequential |
| X-W | Mandatory WebFetch/Context7 → local/version evidence then optional official capability |
| X-M | `model: opus` → inherited session model |
| X-T | Invalid/missing/inherited/contradictory tools → static row T-policy |
| X-O | Missing source output contract → explicitly additive typed contract |
| X-N | Malformed/colliding identity → canonical ID with original retained in provenance |
| X-F | Fixed latest-version assumption → detected compatible project version |
| X-S | Sandbox artifact URI → repository/PR artifact |
| X-E | Anti-bot/CAPTCHA bypass → authorization, API preference, terms/robots compliance, no access-control bypass |
| X-C | Unbounded instruction mutation → generated-block diff plus AP-X |

### 10.3 VUE-03 semantic repair

The only valid approval record is:

```yaml
decision_id: VUE-03-SEMANTIC-REPAIR
decision_owner: user
decision_date: 2026-10-28
source_behavior_disposition: deduplicated-to-vue-component-architect
target_behavior_origin: additive-semantic-repair
adaptation_status: approved
```

Source VUE-03 lines 1–33 are dispositioned as duplicate Vue component behavior consolidated into `vue-component-architect`. The `vue-state-manager` behavior is additive, never represented as source-derived, and uses `source_range: null` plus `design_authority: VUE-03-SEMANTIC-REPAIR`. Its scope is Pinia/Vuex store boundaries, actions/getters/data-flow contracts, persistence, SSR hydration, Vuex-to-Pinia migration, tests, and integration reporting.

### 10.4 Safety dispositions

PY-09 anti-bot/CAPTCHA/access-control evasion, including source lines 1499–1534 where applicable, is `omitted-for-safety` with exact ranges, rationale, and replacement behavior. The replacement requires confirmed authorization, API preference, terms and robots review, respectful rate limits, credentials approval, and no bypass. Destructive migrations, load tests, deployments, infrastructure mutation, credential-bearing scans, and external model/data operations retain useful guidance but are protected by their row risk gates.

## 11. Provenance and licensing

Each target row has a ledger record with this minimum schema:

```yaml
upstream_repository: https://github.com/vijaythecoder/awesome-claude-agents.git
upstream_commit: 2050f3c60fcfea497f7b6b3ec6566cc316367a7e
source_path: <exact-path>
source_blob_sha256: <full-sha256>
source_dispositions:
  - kind: source-derived
    source_range:
      start_line: <integer>
      end_line: <integer>
    destination:
      type: profile | skill | resource | contract | omission-record
      id: <canonical-destination>
    semantic_status: retained | translated | consolidated | corrected | omitted-for-safety
  - kind: additive
    source_range: null
    destination:
      type: profile | skill | resource | contract
      id: <canonical-destination>
    semantic_status: additive
    design_authority: VUE-03-SEMANTIC-REPAIR
source_license_spdx: MIT
source_license_sha256: 6196817dde51dca830403aff706e50aa9929e53a80dc38a1b1636c5926574daa
source_attribution: "Copyright (c) 2024 Awesome Claude Agents Contributors"
adaptation_version: 0.1.0-design.1
target_id: <canonical-public-id>
target_contract_id: <primary-contract-id>
procedure_ids: []
skill_names: []
resource_destinations: []
approval_record: <decision-id-or-null>
```

Every source file is partitioned from line 1 through its exact final line by `source-derived` dispositions with no gaps or overlaps. Their exact integer ranges are mandatory; hashes supplement but never replace them. Safety omissions retain rationale and replacement. The schema validator treats the two disposition kinds as exclusive: `additive` requires `source_range: null` and `design_authority`, while `source-derived` rejects both a null range and additive status. The root `CLAUDE.md` approval lineage records SHA-256 `c2cc9e33425eedfe433d0699d0085e4548897fd33a33ca1cdf51b9b67990eeed` and ranges 101–106 and 189.

The generated distribution includes the MIT license and appropriate upstream attribution. Complete attribution remains in package metadata and the provenance ledger rather than agent-profile comments. No conversion may imply GitHub or original-author endorsement.

## 12. Installation and user documentation

### 12.1 Repository installation

Repository installation copies the portable package's `.github/` tree into the repository root, preserving agents, skills, repository instructions, and applicable path instructions. It supports VS Code/IDE, repository-selected GitHub.com coding-agent sessions, and CLI project discovery. Installation must preview collisions, refuse silent overwrite of non-generated content, and update only files owned by the package manifest. Uninstall removes only digest-matching generated files and leaves user modifications for explicit resolution.

### 12.2 CLI user installation

The CLI user package installs agents to `~/.copilot/agents/` and skills to `~/.copilot/skills/`; documentation may offer `~/.agents/skills/` as the officially documented optional skill destination. It does not install repository/path instructions globally. `COPILOT_HOME` handling follows the pinned CLI documentation. Collisions are shown before replacement and backup/restore behavior is documented.

### 12.3 VS Code user installation

The VS Code package is an import source. Documentation names only the user-profile agent and skill destinations verified for the pinned tested VS Code release and labels them version-sensitive. It does not claim that user installation configures GitHub.com or CLI, and does not ship Local-only handoff metadata in the portable profiles.

### 12.4 Bilingual documentation contract

English and pt-BR documentation both include: purpose and safety boundaries; 33-agent and 21-skill catalogs; routing examples for each surface; repository, CLI-user, and VS Code-user installation/update/uninstall; explicit-selection guidance; permissions and approval policies; MCP/browser optionality; cloud separate-session behavior; troubleshooting; provenance/license; tested platform versions; and release compatibility. Code, canonical IDs, paths, schemas, and commands remain identical. Translation checks ensure matching headings/links and no missing semantic section; English is the normative technical source.

## 13. Validation, smoke tests, and release gates

### 13.1 Structural and generation validation

A release fails unless all of the following hold:

- Canonical schemas validate; exactly 33 unique catalog IDs and filenames exist.
- Exactly PROC-00–PROC-20 exist, with directory and `SKILL.md` names matching the exact §8 values.
- Every agent has the exact frontmatter key set, static tools, approval/risk policy, surface clauses, one primary contract, and Handoff v1.
- Every profile is at most 12,000 Unicode scalar values, with a warning above 8,000, and contains no unresolved tokens, Claude invocation syntax, vendor model, generator comment, sandbox URI, unsafe bypass instruction, unknown tool, or dangling identity.
- All typed contracts validate positive fixtures and reject missing required fields/statuses/unknown agent IDs.
- Provenance partitions every source file exactly, checks source and license hashes, distinguishes additive sections, and records all safety omissions and VUE-03 authority.
- Generation is reproducible from a clean tree and a second run produces no changes.
- Generated root/package inventories and digests match; no stale or unowned generated artifact exists.
- English/pt-BR documentation parity, internal links, official external links, examples, and install manifests validate.

### 13.2 Routing validation

Fixtures cover every row's positive trigger, exclusion, specialist-over-universal precedence, manual-selection requirement, approval policy, risk gate, output contract, and recommended next-agent edge. Cross-cutting fixtures cover unfamiliar repository analysis, complex approval flow, API design-to-framework implementation, review PASS/BLOCK, configuration mutation, visual capability absence, and every dangling-edge substitution. No fixture may rely on undocumented inference scoring.

### 13.3 Surface smoke criteria

Against pinned supported versions:

- **VS Code/IDE:** repository and user package discovery; explicit selection; read-only and writing tool boundaries; one subagent result returning to coordinator when supported; missing-browser fallback; Handoff v1 schema.
- **CLI:** repository and user discovery; `/agent` and `--agent`; skill discovery; tool deny taking precedence; at-most-two coordinator delegation; missing capability and approval fallback; Handoff v1 schema.
- **GitHub.com coding agent:** repository agent and skill discovery; explicit profile selection; repository instructions; work constrained to agent branch/draft PR behavior; no attempted `agent` call; Route Plan recommendation clearly starts a separate session.
- **Installation:** fresh install, idempotent reinstall, generated-file upgrade, collision refusal, digest-safe uninstall, paths containing spaces, and no writes outside selected scope.

Smoke evidence records platform/version, package digest, selected agent, fixture, observed contract/status, artifacts, and disposition. A manual observation is labeled manual; it is not presented as automated evidence.

### 13.4 Release criteria

Release validation compares the authoritative mapping against all 33 IDs, filenames and `name` fields, tools, approvals/risk gates, procedures/skills, contracts, Handoff routing, packages, provenance ranges, and routing fixtures. Required coverage is reported separately: identity 33/33; canonical-ID consistency 33/33; source-line disposition 100%; output contracts 33/33; procedures 21/21; routing/tool/approval rows 33/33; safety omissions 100%; attribution 33/33; package inventory 100%; and surface smoke matrix complete. Any mismatch, undocumented platform claim, placeholder, unapproved additive behavior, failed required smoke, or missing bilingual section blocks release.

## 14. Acceptance criteria

The architecture is accepted only when the future target project demonstrably satisfies all of these conditions:

1. It exposes exactly the 33 IDs and primary contracts in §7, including the five corrected `python-*` IDs and no aliases or 34th public profile.
2. It contains exactly the 21 procedure skills in §8, with PROC IDs and names identical in every catalog, path, package, profile reference, provenance record, and fixture.
3. Portable frontmatter has only `name`, `description`, and explicit `tools`; each row's tools/approval/risk/surface behavior matches §7.
4. Handoff v1 and Route Plan v1 match §9; cloud handoffs always require separately selected sessions.
5. VUE-03 uses only `VUE-03-SEMANTIC-REPAIR`, consolidates duplicated source behavior, and marks all state semantics additive with a null source range.
6. Every source line has one exact disposition; additive and omitted-for-safety behavior is explicit; MIT license and attribution are complete.
7. Profiles are lean, self-contained, deterministic, under the documented character limit, and contain no unresolved build symbols or non-portable promises.
8. Repository, CLI-user, and VS Code-user outputs exactly match §5.2; no personal cloud, organization, or enterprise package is generated.
9. Installation is scoped, collision-safe, idempotent, upgradeable, and digest-safe to uninstall.
10. English and pt-BR reader/install documentation is complete and semantically equivalent, while all prompts and canonical technical identifiers remain English.
11. Routing, validation, safety, generation, installation, and all three surface smoke gates in §13 pass with retained evidence.
12. Release consistency reports all coverage dimensions independently and blocks on any authoritative-mapping difference.
