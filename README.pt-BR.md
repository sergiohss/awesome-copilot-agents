# Awesome Copilot Agents

Distribuição determinística para GitHub Copilot com **33 perfis de agente** e **21 Agent Skills** compartilhadas.

## Conteúdo

- Documentação normativa em inglês em `docs/en/`
- Documentação equivalente para leitores em pt-BR em `docs/pt-BR/`
- Pacotes gerados para repositório, CLI e VS Code em `packages/`

## Início rápido

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/generate.py --release
.venv/bin/python scripts/install.py install repository --target /caminho/do/repositorio
```

## Segurança

Perfis e skills recusam aquisição não autorizada, evasão anti-automação e mutação silenciosa de instruções.

## Proveniência

Fonte upstream: `vijaythecoder/awesome-claude-agents` no commit `2050f3c60fcfea497f7b6b3ec6566cc316367a7e` (MIT).

Consulte `NOTICE` e `provenance/` para o registro completo.
