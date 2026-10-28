# Solução de problemas

## VS Code

Veja [Instalação VS Code](install-vscode.md#solução-de-problemas-vs-code) para descoberta de agentes, skills, subagentes e instruções.

## Instalação no repositório

```bash
.venv/bin/python scripts/install.py install repository --target <raiz-do-repo>
```

**Conflitos de instalação** — o instalador não sobrescreve arquivos que não pertencem ao manifest do pacote. Resolva conflitos manualmente e reinstale.

**Desinstalar** — remove só arquivos com digest correspondente:

```bash
.venv/bin/python scripts/install.py uninstall repository --target <raiz-do-repo>
```

## Geral

- Espere **33** agentes e **21** skills após instalação completa.
- [Catálogo de agentes](agents.md) · [Catálogo de skills](skills.md)
