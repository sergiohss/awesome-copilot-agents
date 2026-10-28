# Instalação e uso no VS Code

Este projeto entrega **33** agentes customizados e **21** Agent Skills para GitHub Copilot no VS Code. A seção [GitHub Copilot no VS Code](../../README.pt-BR.md#-github-copilot-no-vs-code--instalar-e-usar) no README é o guia principal; esta página traz caminhos, verificação e solução de problemas.

## Onde o VS Code procura arquivos

| Customização | Workspace (por repo) | Usuário (todos os workspaces) |
|--------------|----------------------|----------------------------------|
| Agentes customizados | `.github/agents/*.agent.md` | `~/.copilot/agents/*.agent.md` |
| Agent Skills | `.github/skills/<nome>/SKILL.md` | `~/.copilot/skills/<nome>/SKILL.md` (ou `~/.agents/skills/`) |
| Instruções | `.github/copilot-instructions.md` | `~/.copilot/instructions/` (escopo usuário) |

O Copilot harness lê agentes de **usuário** em `~/.copilot/agents`, não em caminhos antigos do user data do perfil VS Code. [Migre](https://code.visualstudio.com/docs/agent-customization/migrate-customizations) se necessário.

## Instalação no workspace (recomendado)

Na raiz de **awesome-copilot-agents**:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/install.py install repository --target /caminho/do/seu/projeto
```

Abra `/caminho/do/seu/projeto` no VS Code. Skills e agentes em `.github/` versionam com o app.

## Instalação no usuário (pacote de importação)

Copie o pacote gerado para VS Code (ainda sem subcomando dedicado no `install.py`):

```bash
ACA=/caminho/para/awesome-copilot-agents
mkdir -p ~/.copilot/agents ~/.copilot/skills
cp -a "$ACA/packages/user/vscode/agents/." ~/.copilot/agents/
cp -a "$ACA/packages/user/vscode/skills/." ~/.copilot/skills/
```

A instalação no usuário **não** copia `.github/copilot-instructions.md`. Use instalação no repositório em cada projeto ou arquivos de instrução próprios.

Manifest de digests: `packages/manifests/user-vscode.json`.

## Usar agentes na visão Chat

1. Abra o Copilot Chat e selecione o modo **Agent**.
2. Escolha um agente no dropdown (`name` no frontmatter YAML = basename do arquivo sem `.agent.md`).
3. Digite `/agents` ou **Chat: Configure Custom Agents** para listar agentes de workspace e usuário.
4. Aprove terminal e edições quando o agente usar ferramentas de escrita.
5. Para trabalho orquestrado, comece com `team-configurator`, depois `tech-lead-orchestrator`; siga os IDs do Route Plan v1.

Consulte [Catálogo de agentes](agents.md) e [Catálogo de skills](skills.md).

## Solução de problemas (VS Code)

| Sintoma | O que verificar |
|---------|-----------------|
| Agentes não aparecem no dropdown | Workspace é a raiz do projeto com `.github/agents`; ou arquivos em `~/.copilot/agents`; nova sessão Agent após copiar |
| Skills não aplicadas | Diretórios com `SKILL.md`; workspace em `.github/skills/aca-*` |
| Só Copilot genérico | Plano com agentes customizados; extensão atualizada; modo Agent ativo |
| Delegação a subagente falha | Orquestrador com ferramenta `agent`; ID alvo existe como `.agent.md` |
| Instruções ignoradas | Instalação no repo inclui `.github/copilot-instructions.md`; só agentes de usuário exigem instruções à parte |

Ao reportar problemas, informe versão do VS Code, extensão Copilot, escopo (workspace vs usuário) e ID do agente selecionado.
