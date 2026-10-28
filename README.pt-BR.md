# Awesome Copilot Agents — Equipe de desenvolvimento para GitHub Copilot 🚀

**Estenda o GitHub Copilot com uma equipe coordenada de 33 agentes customizados** e **21 Agent Skills** compartilhadas — adaptado do [Awesome Claude Agents](https://github.com/vijaythecoder/awesome-claude-agents) para VS Code, Copilot CLI e agente de codificação no GitHub.com.

**Versão em inglês:** [README.md](README.md)

## ⚠️ Aviso importante

- **Trabalho multi-agente pode consumir muitas requisições do Copilot.** Funcionalidades orquestradas podem envolver várias sessões de especialistas, skills e checkpoints de aprovação.
- **Cada superfície se comporta de forma diferente.** VS Code e Copilot CLI podem delegar a subagentes (até **dois especialistas em paralelo**, por política do projeto). **GitHub.com não tem runtime de subagente na mesma sessão** — coordenadores devolvem Route Plans e instruções para sessões separadas, sem afirmar que a delegação já ocorreu.
- **Aprovações fazem parte do desenho.** Pesquisa em trabalho complexo para no gate aprovar/revisar/parar antes da execução. Efeitos externos, operações destrutivas, deploys e mudanças de instrução exigem **aprovação explícita**.
- **Distribuição gerada e auditável.** Perfis e skills em `.github/` e `packages/` vêm de `src/catalog/` — edite o catálogo e regenere; não edite saídas geradas à mão se quiser alinhar com o próximo release.

## 🚀 Início rápido (5 minutos)

### Pré-requisitos

- Assinatura **GitHub Copilot** com **agentes customizados** e **Agent Skills** na sua superfície ([matriz de suporte](https://docs.github.com/en/copilot/reference/customization-cheat-sheet))
- Um **repositório de projeto** onde os agentes devem ficar disponíveis (instalação no repositório)
- **Python 3.11+** (somente se for rodar o instalador ou regenerar pacotes a partir do código)
- **Opcional:** Copilot CLI (`copilot`) ou VS Code com modo agente do Copilot

### 1. Obter a distribuição

```bash
git clone <url-deste-repositorio>
cd awesome-copilot-agents
```

Use `.github/agents` e `.github/skills` **já gerados** neste repositório, ou regenere após alterar o catálogo:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/generate.py --release
```

### 2. Instalar no seu projeto (recomendado)

Na raiz de **awesome-copilot-agents**, instale o pacote portátil no **root do repositório da sua aplicação**:

```bash
.venv/bin/python scripts/install.py install repository --target /caminho/do/seu/projeto
```

Isso copia `.github/agents/`, `.github/skills/` e `.github/copilot-instructions.md` via manifest — **somente arquivos do pacote** são adicionados ou atualizados. Conflitos com arquivos seus são reportados, sem sobrescrita silenciosa.

**Desinstalar** (remove só arquivos gerados com digest correspondente):

```bash
.venv/bin/python scripts/install.py uninstall repository --target /caminho/do/seu/projeto
```

Detalhes: [Instalação no repositório](docs/pt-BR/install-repository.md).

### 3. Verificar a instalação

No seu projeto, confira:

- **33** arquivos em `.github/agents/*.agent.md`
- **21** diretórios de skill em `.github/skills/aca-*/`

No **VS Code** (modo agente) ou **Copilot CLI**, os agentes customizados devem aparecer para seleção (a UI depende da versão do Copilot).

### 4. Inicializar a equipe do projeto

Abra o **diretório do projeto** no Copilot e selecione o agente **`team-configurator`**. Exemplo de prompt:

```text
Detecte a stack deste repositório e mostre uma prévia de configuração da equipe de IA para .github/copilot-instructions.md. Não altere instruções até eu aprovar a prévia.
```

O configurador preserva texto seu fora do bloco gerado e exige **aprovação explícita** antes de editar instruções.

### 5. Começar a construir

Para funcionalidades multi-etapa, comece pelo orquestrador:

**VS Code / GitHub.com (agente selecionado na UI):**

```text
Analise este pedido e devolva Route Plan v1 com IDs exatos de especialistas, dependências e checkpoints de aprovação: construir um sistema de autenticação de usuários.
```

Agente: **`tech-lead-orchestrator`**

**Copilot CLI:**

```bash
copilot --agent tech-lead-orchestrator "Devolva Route Plan v1 para um sistema de autenticação neste repositório"
```

Siga o Route Plan: use **somente** os IDs listados, respeite o limite de dois agentes em paralelo no IDE/CLI e acione **`code-reviewer`** (ou outros gates) quando o plano indicar.

## 💻 GitHub Copilot no VS Code — instalar e usar

Estes agentes são **agentes customizados do Copilot** (perfis `.agent.md`) mais **Agent Skills** em `.github/skills/` ou `~/.copilot/skills/`. O VS Code os descobre quando você usa o **Copilot Chat no modo Agente** (Copilot harness).

Referências oficiais: [Custom agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents) · [Agent mode](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-agent-mode) · [Subagents](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents)

### Pré-requisitos (VS Code)

- Plano **GitHub Copilot** ativo com **agentes customizados** e **Agent Skills**
- **VS Code** com extensão GitHub Copilot Chat (versão recente com modo **Agent**)
- Uma pasta aberta como workspace — o repositório da aplicação (após instalação no repo) ou qualquer pasta se usar agentes no perfil do usuário

Se você guardava agentes no user data do perfil do VS Code, migre para as pastas nativas do Copilot: [Migrate customizations](https://code.visualstudio.com/docs/agent-customization/migrate-customizations) (`~/.copilot/agents`, `~/.copilot/skills`).

### Instalação para o VS Code

| Escopo | Onde ficam os arquivos | Quando usar |
|--------|-------------------------|-------------|
| **Workspace (recomendado)** | `<seu-repo>/.github/agents/`, `.github/skills/`, `.github/copilot-instructions.md` | Equipe compartilha os 33 agentes + skills via git; instruções valem para aquele repo |
| **Usuário (todos os workspaces)** | `~/.copilot/agents/`, `~/.copilot/skills/` | Cópia pessoal em todo projeto, sem commitar `.github/` |

#### Instalação no workspace (recomendado)

Na raiz de **awesome-copilot-agents**, execute o passo **2** acima (`scripts/install.py install repository --target …`) e **abra a raiz desse projeto no VS Code**. O Copilot lê agentes do workspace em `.github/agents/` e skills em `.github/skills/`.

Verifique no projeto:

```bash
ls .github/agents/*.agent.md | wc -l    # espere 33
ls -d .github/skills/aca-* | wc -l      # espere 21
```

#### Instalação no usuário (copiar pacote de importação)

A origem gerada é `packages/user/vscode/`. Copie agentes e skills para as pastas de usuário do Copilot (**não** instala instruções de repositório globalmente):

**macOS / Linux:**

```bash
ACA=/caminho/para/awesome-copilot-agents
mkdir -p ~/.copilot/agents ~/.copilot/skills
cp -a "$ACA/packages/user/vscode/agents/." ~/.copilot/agents/
cp -a "$ACA/packages/user/vscode/skills/." ~/.copilot/skills/
```

**Windows (PowerShell):**

```powershell
$ACA = "C:\caminho\para\awesome-copilot-agents"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.copilot\agents", "$env:USERPROFILE\.copilot\skills"
Copy-Item -Recurse -Force "$ACA\packages\user\vscode\agents\*" "$env:USERPROFILE\.copilot\agents\"
Copy-Item -Recurse -Force "$ACA\packages\user\vscode\skills\*" "$env:USERPROFILE\.copilot\skills\"
```

Para instruções por repositório usando só agentes de usuário, faça **instalação no repositório** em cada app ou mantenha `.github/copilot-instructions.md` / `~/.copilot/instructions` — veja [Instalação VS Code](docs/pt-BR/install-vscode.md).

### Usar agentes no VS Code

1. **Abra o workspace** — pasta do app com `.github/agents`, ou qualquer pasta se instalou no usuário.
2. **Abra o Copilot Chat** — visão Chat na barra lateral.
3. **Ative o modo Agente** — controle de modo no chat (Agente, não só Ask/Edit). O modo Agente habilita ferramentas, skills e delegação a subagentes.
4. **Selecione um agente customizado** — **dropdown de agentes** na parte inferior do chat. Escolha pelo ID canônico (nome do arquivo sem `.agent.md`), por exemplo `tech-lead-orchestrator`, `django-api-developer`, `code-reviewer`.
5. **Gerenciar agentes** — digite **`/agents`** no chat ou **Chat: Configure Custom Agents** na Paleta de Comandos (`Ctrl+Shift+P`). Os agentes deste pacote já estarão no disco após a instalação.
6. **Aprove ferramentas** — comandos de terminal e edições pedem confirmação; agentes read-only (ex.: `code-reviewer`) ficam em read/search conforme o perfil.
7. **Subagentes (IDE)** — orquestradores com ferramenta `agent` podem delegar a outro agente na mesma sessão (política do projeto: **no máximo dois** especialistas em paralelo). Siga os IDs exatos do Route Plan.
8. **Recarregar se preciso** — após copiar arquivos, inicie uma **nova sessão Agent** ou recarregue a janela para descobrir os 33 agentes.

### Fluxo sugerido no VS Code

| Etapa | Agente | O que pedir |
|-------|--------|-------------|
| 1 — Configurar equipe | `team-configurator` | Detectar stack e **prévia** de `.github/copilot-instructions.md`; aprovar antes de editar |
| 2 — Planejar feature | `tech-lead-orchestrator` | **Route Plan v1** com IDs, dependências e checkpoints |
| 3 — Implementar fatias | Especialistas do plano | Uma tarefa delimitada por sessão |
| 4 — Gate de qualidade | `code-reviewer` | Revisar paths alterados; **code-review-v1** PASS/BLOCK |

Exemplo com **`tech-lead-orchestrator`** no dropdown:

```text
Analise este repositório e devolva Route Plan v1 para login OAuth2 com refresh tokens. Inclua IDs exatos de especialistas, dependências, grupos de concorrência (máx. dois em paralelo) e onde code-reviewer deve rodar.
```

Mais detalhes: [docs/pt-BR/install-vscode.md](docs/pt-BR/install-vscode.md) · [Solução de problemas](docs/pt-BR/troubleshooting.md#vs-code)

## 🎯 Como funciona a auto-configuração

Com o **`team-configurator`**:

1. **Lê evidências de stack** — arquivos de dependência e build
2. **Mapeia tarefas para IDs canônicos** — especialistas de framework antes de fallbacks universais; inclui gates como **`code-reviewer`** quando couber
3. **Mostra prévia de instruções** — bloco gerado para `.github/copilot-instructions.md` sem edição silenciosa
4. **Aguarda aprovação** — só muta instruções ou catálogo após você aprovar
5. **Devolve `team-configuration-v1`** — stack, agentes escolhidos e rationale em Handoff v1 tipado

Detalhes progressivos ficam nas **Agent Skills** — os agentes carregam skills conforme necessário.

## 👥 Conheça a equipe de IA

IDs canônicos = nomes de arquivo: `.github/agents/<id>.agent.md`.

### 🎭 Orquestradores (3 agentes)

- **[tech-lead-orchestrator](.github/agents/tech-lead-orchestrator.agent.md)** — Liderança técnica; **Route Plan v1** (planeja e roteia, não implementa fatias de produto)
- **[project-analyst](.github/agents/project-analyst.agent.md)** — Inspeção de repositório; **stack-analysis-v1**
- **[team-configurator](.github/agents/team-configurator.agent.md)** — Configuração da equipe de IA; prévia + aprovação antes de mutação

### 🔧 Equipe core (4 agentes)

- **[code-archaeologist](.github/agents/code-archaeologist.agent.md)** — Codebases legadas; **codebase-assessment-v1**
- **[code-reviewer](.github/agents/code-reviewer.agent.md)** — Revisão read-only com segurança; **code-review-v1** PASS/BLOCK
- **[performance-optimizer](.github/agents/performance-optimizer.agent.md)** — Performance cross-stack; delega ORM/runtime a especialistas
- **[documentation-specialist](.github/agents/documentation-specialist.agent.md)** — Lacunas de documentação; **documentation-changelog-v1**

### 🌐 Especialistas universais (4 agentes)

- **[api-architect](.github/agents/api-architect.agent.md)** — Contratos REST/GraphQL independentes de framework
- **[backend-developer](.github/agents/backend-developer.agent.md)** — Fallback server-side poliglota
- **[frontend-developer](.github/agents/frontend-developer.agent.md)** — Fallback de UI quando React/Vue não são donos
- **[tailwind-css-expert](.github/agents/tailwind-css-expert.agent.md)** — Tailwind, temas e componentes acessíveis

### 💼 Especialistas de framework (13 agentes)

- **Laravel (2)** — [laravel-backend-expert](.github/agents/laravel-backend-expert.agent.md), [laravel-eloquent-expert](.github/agents/laravel-eloquent-expert.agent.md)
- **Django (3)** — [django-backend-expert](.github/agents/django-backend-expert.agent.md), [django-api-developer](.github/agents/django-api-developer.agent.md), [django-orm-expert](.github/agents/django-orm-expert.agent.md)
- **Rails (3)** — [rails-backend-expert](.github/agents/rails-backend-expert.agent.md), [rails-api-developer](.github/agents/rails-api-developer.agent.md), [rails-activerecord-expert](.github/agents/rails-activerecord-expert.agent.md)
- **React (2)** — [react-component-architect](.github/agents/react-component-architect.agent.md), [react-nextjs-expert](.github/agents/react-nextjs-expert.agent.md)
- **Vue (3)** — [vue-component-architect](.github/agents/vue-component-architect.agent.md), [vue-nuxt-expert](.github/agents/vue-nuxt-expert.agent.md), [vue-state-manager](.github/agents/vue-state-manager.agent.md)

### 🐍 Especialistas Python (9 agentes)

- **[python-expert](.github/agents/python-expert.agent.md)** — Python geral
- **[fastapi-expert](.github/agents/fastapi-expert.agent.md)** — FastAPI/Pydantic
- **[django-expert](.github/agents/django-expert.agent.md)** — Django full-stack integrador
- **[ml-data-expert](.github/agents/ml-data-expert.agent.md)** — ML/dados reprodutíveis
- **[python-devops-cicd-expert](.github/agents/python-devops-cicd-expert.agent.md)** — CI/CD, containers, IaC
- **[python-performance-expert](.github/agents/python-performance-expert.agent.md)** — Profiling Python
- **[python-security-expert](.github/agents/python-security-expert.agent.md)** — Avaliação de segurança read-only
- **[python-testing-expert](.github/agents/python-testing-expert.agent.md)** — Estratégia de testes
- **[python-web-scraping-expert](.github/agents/python-web-scraping-expert.agent.md)** — Aquisição **autorizada** apenas

**Total: 33 agentes** e **21 skills** (`aca-*` em `.github/skills/`).

Catálogo: [docs/pt-BR/agents.md](docs/pt-BR/agents.md) · [docs/pt-BR/skills.md](docs/pt-BR/skills.md)

## 📦 Outros alvos de instalação

| Alvo | Local | Notas |
|------|-------|--------|
| **Repositório** (recomendado) | `.github/` do repo | `scripts/install.py install repository --target …` |
| **Usuário Copilot CLI** | `~/.copilot/agents/`, `~/.copilot/skills/` | Importar de `packages/user/cli/` — [CLI](docs/pt-BR/install-cli.md) |
| **Usuário VS Code** | Caminhos sensíveis à versão | Importar de `packages/user/vscode/` — [VS Code](docs/pt-BR/install-vscode.md) |

## 🧠 Agent Skills (21 procedimentos)

Skills guardam PROC-00 … PROC-20 para perfis enxutos. Exemplos: `aca-core-orchestration`, `aca-deterministic-agent-routing`, `aca-human-approval-checkpoint`, `aca-severity-based-code-review`, `aca-bounded-instruction-update`. Lista completa: `src/catalog/procedures.yaml`.

## 🔥 Por que equipe vence agente genérico

- **Profundidade por domínio** — Contratos tipados e políticas de ferramentas por papel
- **Orquestração honesta** — Handoff v1 em vez de delegação fictícia
- **Carregamento progressivo** — Skills trazem procedimentos longos sob demanda
- **Segurança** — Revisão, deploy e scraping com PASS/BLOCK e aprovações

## 📚 Saiba mais

- [Arquitetura](docs/design/architecture.md) (normativo, inglês)
- [Compatibilidade](docs/pt-BR/compatibility.md)
- [Solução de problemas](docs/pt-BR/troubleshooting.md)
- [Contribuindo](CONTRIBUTING.md)

## 🛡️ Segurança

Recusa de aquisição não autorizada, evasão anti-automação e mutação silenciosa de instruções.

## 📜 Proveniência e licença

Adaptado de **Awesome Claude Agents** (MIT), commit `2050f3c60fcfea497f7b6b3ec6566cc316367a7e`. Veja [NOTICE](NOTICE) e [`provenance/`](provenance/).

**Licença:** MIT — [LICENSE](LICENSE).

---

<p align="center">
  <strong>GitHub Copilot como equipe de especialistas, com roteamento e aprovações explícitas</strong><br>
  <em>Instale no repositório, configure uma vez, orquestre com <code>tech-lead-orchestrator</code>.</em>
</p>

<p align="center">
  <a href="docs/pt-BR/install-vscode.md">VS Code</a> •
  <a href="docs/pt-BR/install-repository.md">Instalar</a> •
  <a href="docs/design/architecture.md">Arquitetura</a> •
  <a href="README.md">English</a>
</p>
