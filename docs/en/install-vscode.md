# VS Code installation and usage

This project ships **33** custom agents and **21** Agent Skills for GitHub Copilot in VS Code. The README section [GitHub Copilot in VS Code](../README.md#-github-copilot-in-vs-code--install-and-use) is the primary guide; this page adds paths, verification, and troubleshooting.

## Where VS Code looks for files

| Customization | Workspace (per repo) | User (all workspaces) |
|---------------|----------------------|------------------------|
| Custom agents | `.github/agents/*.agent.md` | `~/.copilot/agents/*.agent.md` |
| Agent Skills | `.github/skills/<name>/SKILL.md` | `~/.copilot/skills/<name>/SKILL.md` (or `~/.agents/skills/`) |
| Instructions | `.github/copilot-instructions.md` | `~/.copilot/instructions/` (user scope) |

Agent Host / Copilot harness reads **user** agents from `~/.copilot/agents`, not from legacy VS Code profile user-data paths. [Migrate](https://code.visualstudio.com/docs/agent-customization/migrate-customizations) if needed.

## Workspace install (recommended)

From the root of **awesome-copilot-agents**:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/install.py install repository --target /path/to/your/project
```

Open `/path/to/your/project` in VS Code. Skills and agents under `.github/` are versioned with your app.

## User install (import bundle)

Copy the generated VS Code user package (no `install.py` subcommand yet):

```bash
ACA=/path/to/awesome-copilot-agents
mkdir -p ~/.copilot/agents ~/.copilot/skills
cp -a "$ACA/packages/user/vscode/agents/." ~/.copilot/agents/
cp -a "$ACA/packages/user/vscode/skills/." ~/.copilot/skills/
```

User install does **not** copy `.github/copilot-instructions.md`. Use repository install on each project for team instructions, or add your own instruction files.

Manifest for digests: `packages/manifests/user-vscode.json`.

## Using agents in the Chat view

1. Open Copilot Chat and select **Agent** mode.
2. Choose an agent from the dropdown (canonical `name` in YAML frontmatter = file basename without `.agent.md`).
3. Type `/agents` or run **Chat: Configure Custom Agents** to list workspace and user agents.
4. Approve terminal and edit prompts when agents use write tools.
5. For orchestrated work, start with `team-configurator`, then `tech-lead-orchestrator`; follow Route Plan v1 specialist IDs.

See [Agent catalog](agents.md) and [Skill catalog](skills.md).

## Troubleshooting (VS Code)

| Symptom | What to check |
|---------|----------------|
| Agents missing in dropdown | Folder open is project root with `.github/agents`; or user files in `~/.copilot/agents`; start a **new** Agent session after copying files |
| Skills not applied | Skill directories must contain `SKILL.md`; workspace skills live under `.github/skills/aca-*` |
| Only generic Copilot, no custom names | Copilot plan includes custom agents; extension updated; Agent mode enabled |
| Subagent delegation fails | Orchestrator profile includes `agent` tool; target ID matches an installed `.agent.md` file |
| Instructions ignored | Repository install includes `.github/copilot-instructions.md`; user-only agent install needs separate instructions |

Report issues with VS Code version, Copilot extension version, install scope (workspace vs user), and agent ID selected.
