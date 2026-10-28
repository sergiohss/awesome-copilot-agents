# Troubleshooting

## VS Code

See the [VS Code install guide](install-vscode.md#troubleshooting-vs-code) for agent discovery, skills, subagents, and instructions.

## Repository install

```bash
.venv/bin/python scripts/install.py install repository --target <repo-root>
```

**Install conflicts** — the installer refuses to overwrite files not owned by the package manifest. Resolve conflicts manually or move your files, then reinstall.

**Uninstall** — only removes files whose digest matches the install manifest:

```bash
.venv/bin/python scripts/install.py uninstall repository --target <repo-root>
```

## General

- Expect **33** agents and **21** skills after a full install.
- [Agent catalog](agents.md) · [Skill catalog](skills.md)
