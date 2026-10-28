# Awesome Copilot Agents

Deterministic GitHub Copilot distribution with **33 agent profiles** and **21 shared Agent Skills**.

## Contents

- English normative documentation under `docs/en/`
- Equivalent pt-BR reader documentation under `docs/pt-BR/`
- Generated repository, CLI, and VS Code packages under `packages/`

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/generate.py --release
.venv/bin/python scripts/install.py install repository --target /path/to/repo
```

## Safety

Profiles and skills refuse unauthorized acquisition, anti-automation evasion, and silent instruction mutation.

## Provenance

Upstream source: `vijaythecoder/awesome-claude-agents` at commit `2050f3c60fcfea497f7b6b3ec6566cc316367a7e` (MIT).

See `NOTICE` and `provenance/` for the full ledger.
