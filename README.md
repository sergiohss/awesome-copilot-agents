# Awesome Copilot Agents — AI Development Team for GitHub Copilot 🚀

**Give GitHub Copilot a coordinated team of 33 specialized custom agents** plus **21 shared Agent Skills** — adapted from [Awesome Claude Agents](https://github.com/vijaythecoder/awesome-claude-agents) for VS Code, Copilot CLI, and GitHub.com coding agent workflows.

**Also available in Portuguese:** [README.pt-BR.md](README.pt-BR.md)

## ⚠️ Important Notice

- **Multi-agent work can consume many Copilot requests.** Orchestrated features may involve several specialist sessions, skills, and approval checkpoints — plan accordingly.
- **Surfaces behave differently.** VS Code and Copilot CLI can delegate to subagents (up to **two concurrent** specialists by project policy). **GitHub.com has no in-session subagent runtime** — coordinators return Route Plans and separate-session instructions instead of claiming delegation already ran.
- **Approvals are part of the design.** Research for complex work stops at an approve/revise/stop gate before execution. External effects, destructive operations, deploys, and instruction changes require **explicit approval**.
- **Generated, auditable distribution.** Agent profiles and skills under `.github/` and `packages/` are built from `src/catalog/` — edit the catalog and regenerate; do not hand-edit generated outputs unless you accept drift from the next release.

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- **GitHub Copilot** subscription with access to **custom agents** and **Agent Skills** on your surface ([support matrix](https://docs.github.com/en/copilot/reference/customization-cheat-sheet))
- A **project repository** where you want agents available (for repository install)
- **Python 3.11+** (only if you run the installer or regenerate packages from source)
- **Optional:** Copilot CLI (`copilot`) or VS Code with Copilot agent mode for local delegation

### 1. Get the distribution

```bash
git clone <this-repository-url>
cd awesome-copilot-agents
```

Use the **pre-generated** `.github/agents` and `.github/skills` in this repo, or regenerate after changing the catalog:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/generate.py --release
```

### 2. Install into your project (recommended)

From the root of **awesome-copilot-agents**, install the portable repository package into **your app’s repo root**:

```bash
.venv/bin/python scripts/install.py install repository --target /path/to/your/project
```

This copies `.github/agents/`, `.github/skills/`, and `.github/copilot-instructions.md` using a manifest so **only package-owned files** are added or updated. Conflicts with your existing files are reported instead of silently overwritten.

**Uninstall** (removes only digest-matching generated files):

```bash
.venv/bin/python scripts/install.py uninstall repository --target /path/to/your/project
```

See [Repository installation](docs/en/install-repository.md) for details.

### 3. Verify installation

In your project, confirm:

- **33** files in `.github/agents/*.agent.md`
- **21** skill directories under `.github/skills/aca-*/`

In **VS Code** agent mode or **Copilot CLI**, your custom agents should appear for selection (exact UI depends on your Copilot version).

### 4. Initialize your project team

Open your **project directory** in Copilot and select the **`team-configurator`** agent (or equivalent picker on your surface). Example prompt:

```text
Detect the stack from this repository and preview an AI team configuration update for .github/copilot-instructions.md. Do not mutate instructions until I approve the preview.
```

The configurator preserves your prose outside the generated block and requires **explicit approval** before editing instructions.

### 5. Start building

For multi-step features, start with the orchestrator — example prompts:

**VS Code / GitHub.com (agent selected in UI):**

```text
Analyze this request and return Route Plan v1 with exact specialist IDs, dependencies, and approval checkpoints: build a user authentication system.
```

Select agent: **`tech-lead-orchestrator`**

**Copilot CLI:**

```bash
copilot --agent tech-lead-orchestrator "Return Route Plan v1 for a user authentication system in this repo"
```

Follow the Route Plan: use **only** the listed specialist IDs, respect the two-agent concurrency cap on IDE/CLI, and run **`code-reviewer`** (or other gates) when the plan says so.

## 💻 GitHub Copilot in VS Code — install and use

These agents are **custom Copilot agents** (`.agent.md` profiles) plus **Agent Skills** under `.github/skills/` or `~/.copilot/skills/`. VS Code discovers them when you use **Copilot Chat in Agent mode** with the Copilot harness.

Official references: [Custom agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents) · [Agent mode](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-agent-mode) · [Subagents](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents)

### Prerequisites (VS Code)

- Active **GitHub Copilot** plan with **custom agents** and **Agent Skills** on your account
- **VS Code** with GitHub Copilot Chat extension (recent release with **Agent** mode)
- A folder opened as workspace — either your app repo (after repository install) or any workspace if you use user-level agents

If you previously stored agents in VS Code profile user data, migrate them to native Copilot folders: [Migrate customizations](https://code.visualstudio.com/docs/agent-customization/migrate-customizations) (`~/.copilot/agents`, `~/.copilot/skills`).

### Install for VS Code

| Scope | Where files go | When to use |
|-------|----------------|-------------|
| **Workspace (recommended)** | `<your-repo>/.github/agents/`, `.github/skills/`, `.github/copilot-instructions.md` | Team shares the same 33 agents + skills via git; instructions apply to that repo |
| **User (all workspaces)** | `~/.copilot/agents/`, `~/.copilot/skills/` | Personal copy available in every project without committing `.github/` |

#### Workspace install (recommended)

From **awesome-copilot-agents**, run step **2** above (`scripts/install.py install repository --target …`), then **open that project root in VS Code**. Copilot reads workspace agents from `.github/agents/` and skills from `.github/skills/` (or `.agents/skills/` if you use that layout).

Verify in the project:

```bash
ls .github/agents/*.agent.md | wc -l    # expect 33
ls -d .github/skills/aca-* | wc -l      # expect 21
```

#### User install (copy import bundle)

The generated import source is `packages/user/vscode/`. Copy agents and skills into Copilot’s user folders (does **not** install repository instructions globally):

**macOS / Linux:**

```bash
ACA=/path/to/awesome-copilot-agents
mkdir -p ~/.copilot/agents ~/.copilot/skills
cp -a "$ACA/packages/user/vscode/agents/." ~/.copilot/agents/
cp -a "$ACA/packages/user/vscode/skills/." ~/.copilot/skills/
```

**Windows (PowerShell):**

```powershell
$ACA = "C:\path\to\awesome-copilot-agents"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.copilot\agents", "$env:USERPROFILE\.copilot\skills"
Copy-Item -Recurse -Force "$ACA\packages\user\vscode\agents\*" "$env:USERPROFILE\.copilot\agents\"
Copy-Item -Recurse -Force "$ACA\packages\user\vscode\skills\*" "$env:USERPROFILE\.copilot\skills\"
```

For per-repo instructions with user-level agents only, either run **repository install** on each app repo or maintain your own `.github/copilot-instructions.md` / `~/.copilot/instructions` — see [VS Code install guide](docs/en/install-vscode.md).

### Use agents in VS Code

1. **Open the workspace** — the app folder where `.github/agents` lives, or any folder if you used user install.
2. **Open Copilot Chat** — Chat view in the activity bar (or your configured keybinding).
3. **Switch to Agent mode** — use the mode control in chat (Agent, not only Ask/Edit). Agent mode enables tools, skills, and subagent delegation.
4. **Select a custom agent** — use the **agents dropdown** at the bottom of the chat input. Pick by canonical ID (matches filename without `.agent.md`), for example `tech-lead-orchestrator`, `django-api-developer`, `code-reviewer`.
5. **Manage agents** — type **`/agents`** in chat or run **Chat: Configure Custom Agents** from the Command Palette (`Ctrl+Shift+P` / `⇧⌘P`). Use **New Agent (Workspace)** vs **New Agent (User)** only for your own agents; this package’s agents are already on disk after install.
6. **Approve tools** — when an agent runs terminal commands or edits files, VS Code prompts for approval; read-only agents (for example `code-reviewer`) stay within read/search tools per profile.
7. **Subagents (IDE)** — orchestrators with the `agent` tool may delegate to another custom agent in the same session (project policy: **at most two** specialists in parallel). Follow the Route Plan’s exact IDs; do not substitute generic agents when a framework specialist is listed.
8. **Reload if needed** — after copying new files, start a **new Agent chat session** or reload the window so discovery picks up all 33 agents.

### Suggested VS Code workflow

| Step | Agent | What to ask |
|------|--------|-------------|
| 1 — Configure team | `team-configurator` | Detect stack and **preview** updates to `.github/copilot-instructions.md`; approve before any edit |
| 2 — Plan feature | `tech-lead-orchestrator` | Return **Route Plan v1** with specialist IDs, dependencies, and approval checkpoints |
| 3 — Implement slices | Specialists from the plan | One bounded task per session (for example `fastapi-expert`, `react-component-architect`) |
| 4 — Quality gate | `code-reviewer` | Review changed paths; expect **code-review-v1** with PASS/BLOCK |

Example with **`tech-lead-orchestrator`** selected in the agents dropdown:

```text
Analyze this repository and return Route Plan v1 for adding OAuth2 login with refresh tokens. Include exact specialist IDs, dependencies, concurrency groups (max two parallel), and where code-reviewer must run.
```

More detail: [docs/en/install-vscode.md](docs/en/install-vscode.md) · [Troubleshooting](docs/en/troubleshooting.md#vs-code)

## 🎯 How auto-configuration works

When you use **`team-configurator`**, it:

1. **Reads stack evidence** — dependency and build files (`package.json`, `composer.json`, `requirements.txt`, `go.mod`, `Gemfile`, etc.)
2. **Maps tasks to canonical agent IDs** — prefers framework specialists over universal fallbacks; keeps quality gates such as **`code-reviewer`** and **`performance-optimizer`** where appropriate
3. **Previews instruction updates** — shows the generated block for `.github/copilot-instructions.md` without silent edits
4. **Waits for approval** — mutates instructions or catalogs only after you explicitly approve
5. **Returns `team-configuration-v1`** — stack summary, selected agents, and rationale in a typed Handoff v1 contract

Progressive detail lives in **Agent Skills** (`aca-stack-detection-with-confidence`, `aca-bounded-instruction-update`, etc.) — agents load skills as needed instead of stuffing every procedure into the profile prompt.

## 👥 Meet your AI development team

Canonical IDs match filenames: `.github/agents/<id>.agent.md`.

### 🎭 Orchestrators (3 agents)

- **[tech-lead-orchestrator](.github/agents/tech-lead-orchestrator.agent.md)** — Senior lead for complex work; returns **Route Plan v1** with specialist assignments, dependencies, concurrency groups, and approval checkpoints (plans only — does not implement product slices)
- **[project-analyst](.github/agents/project-analyst.agent.md)** — Repository inspector; returns **stack-analysis-v1** with evidence, confidence, unknowns, and specialist recommendations
- **[team-configurator](.github/agents/team-configurator.agent.md)** — Prepares bounded AI team configuration updates; previews instruction blocks and requires approval before mutation

### 🔧 Core team (4 agents)

- **[code-archaeologist](.github/agents/code-archaeologist.agent.md)** — Legacy and unfamiliar codebases; **codebase-assessment-v1**
- **[code-reviewer](.github/agents/code-reviewer.agent.md)** — Read-only, security-aware reviews; **code-review-v1** with PASS/BLOCK
- **[performance-optimizer](.github/agents/performance-optimizer.agent.md)** — Cross-stack performance lifecycle (baseline → profile → compare); defers ORM/runtime depth to narrower specialists
- **[documentation-specialist](.github/agents/documentation-specialist.agent.md)** — Reader-facing docs gaps; **documentation-changelog-v1**

### 🌐 Universal experts (4 agents)

- **[api-architect](.github/agents/api-architect.agent.md)** — Technology-independent REST/GraphQL contracts before implementation
- **[backend-developer](.github/agents/backend-developer.agent.md)** — Polyglot server-side fallback when no framework specialist owns the work
- **[frontend-developer](.github/agents/frontend-developer.agent.md)** — Universal UI fallback when no React/Vue specialist owns the work
- **[tailwind-css-expert](.github/agents/tailwind-css-expert.agent.md)** — Tailwind utilities, themes, and accessible component delivery

### 💼 Framework specialists (13 agents)

- **Laravel (2)** — [laravel-backend-expert](.github/agents/laravel-backend-expert.agent.md), [laravel-eloquent-expert](.github/agents/laravel-eloquent-expert.agent.md)
- **Django (3)** — [django-backend-expert](.github/agents/django-backend-expert.agent.md), [django-api-developer](.github/agents/django-api-developer.agent.md), [django-orm-expert](.github/agents/django-orm-expert.agent.md)
- **Rails (3)** — [rails-backend-expert](.github/agents/rails-backend-expert.agent.md), [rails-api-developer](.github/agents/rails-api-developer.agent.md), [rails-activerecord-expert](.github/agents/rails-activerecord-expert.agent.md)
- **React (2)** — [react-component-architect](.github/agents/react-component-architect.agent.md), [react-nextjs-expert](.github/agents/react-nextjs-expert.agent.md)
- **Vue (3)** — [vue-component-architect](.github/agents/vue-component-architect.agent.md), [vue-nuxt-expert](.github/agents/vue-nuxt-expert.agent.md), [vue-state-manager](.github/agents/vue-state-manager.agent.md)

### 🐍 Python specialists (9 agents)

- **[python-expert](.github/agents/python-expert.agent.md)** — General Python when no narrower owner applies
- **[fastapi-expert](.github/agents/fastapi-expert.agent.md)** — FastAPI/Pydantic async APIs
- **[django-expert](.github/agents/django-expert.agent.md)** — Full-stack Django integrator (templates, admin, DRF, Celery, architecture)
- **[ml-data-expert](.github/agents/ml-data-expert.agent.md)** — Reproducible ML/data pipelines and evaluation
- **[python-devops-cicd-expert](.github/agents/python-devops-cicd-expert.agent.md)** — CI/CD, containers, IaC with deploy approval gates
- **[python-performance-expert](.github/agents/python-performance-expert.agent.md)** — Python runtime profiling and regression disposition
- **[python-security-expert](.github/agents/python-security-expert.agent.md)** — Read-only Python security assessment (PASS/BLOCK)
- **[python-testing-expert](.github/agents/python-testing-expert.agent.md)** — Layered testing strategy, fixtures, mutation/coverage gates
- **[python-web-scraping-expert](.github/agents/python-web-scraping-expert.agent.md)** — **Authorized** acquisition only (APIs, robots/terms, rate limits)

**Total: 33 agents** and **21 skills** (`aca-*` under `.github/skills/`).

Browse the full catalog: [docs/en/agents.md](docs/en/agents.md) · [docs/en/skills.md](docs/en/skills.md)

## 📦 Other installation targets

| Target | Location | Notes |
|--------|----------|--------|
| **Repository** (recommended) | Your repo’s `.github/` | `scripts/install.py install repository --target …` |
| **Copilot CLI user** | `~/.copilot/agents/`, `~/.copilot/skills/` | Import from `packages/user/cli/` — see [CLI install](docs/en/install-cli.md) |
| **VS Code user** | Version-sensitive user profile paths | Import from `packages/user/vscode/` — see [VS Code install](docs/en/install-vscode.md) |

Repository install enables **GitHub.com coding agent** discovery for that repo. User packages do **not** configure cloud or CLI globally by themselves.

## 🧠 Agent Skills (21 procedures)

Skills hold reusable procedures (PROC-00 … PROC-20) so profiles stay under Copilot’s size limits. Examples:

| Skill | Purpose |
|-------|---------|
| `aca-core-orchestration` | Route Plan v1, Handoff v1, routing precedence, surface fallbacks |
| `aca-deterministic-agent-routing` | Exact specialist IDs, exclusions, dependencies |
| `aca-human-approval-checkpoint` | Approve/revise/stop before complex execution |
| `aca-severity-based-code-review` | Evidence-backed review disposition |
| `aca-bounded-instruction-update` | Generated-block-only instruction updates |

Full list: `src/catalog/procedures.yaml` and generated `.github/skills/`.

## 🔥 Why teams beat a single generic agent

- **Specialist depth** — Framework and domain agents encode conventions, contracts, and tool policies (least privilege per role)
- **Honest orchestration** — Typed Handoff v1 results instead of vague “I asked another agent” claims
- **Progressive loading** — Skills bring in long procedures only when needed
- **Safety by default** — Review, security, deploy, and scraping agents enforce PASS/BLOCK and approval boundaries

## 📈 What you get

- **Faster complex features** — Clear routing from orchestrator → specialists → review gates
- **Consistent stack choices** — Prefer `django-api-developer` over generic `backend-developer` when evidence supports it
- **Auditable lineage** — Catalog, provenance ledger, and deterministic generation from source

## 📚 Learn more

- [Architecture & conversion spec](docs/design/architecture.md) — normative design (English)
- [Compatibility & surfaces](docs/en/compatibility.md)
- [Troubleshooting](docs/en/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- Portuguese reader docs: [docs/pt-BR/](docs/pt-BR/)

## 🛡️ Safety

Profiles and skills **refuse** unauthorized acquisition, anti-automation evasion, and silent instruction mutation. **`python-web-scraping-expert`** is for authorized pipelines only.

## 📜 Provenance & license

Adapted from **Awesome Claude Agents** (MIT), upstream commit `2050f3c60fcfea497f7b6b3ec6566cc316367a7e`. See [NOTICE](NOTICE) and [`provenance/`](provenance/) for the full ledger.

**License:** MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <strong>Turn GitHub Copilot into a specialist development team with explicit routing and approvals</strong><br>
  <em>Install into your repo, configure once, then orchestrate with <code>tech-lead-orchestrator</code>.</em>
</p>

<p align="center">
  <a href="docs/en/install-vscode.md">VS Code</a> •
  <a href="docs/en/install-repository.md">Install</a> •
  <a href="docs/design/architecture.md">Architecture</a> •
  <a href="README.pt-BR.md">Português</a>
</p>
