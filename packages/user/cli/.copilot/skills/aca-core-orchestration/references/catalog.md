# Canonical 33-agent catalog

| agent_id | contract_id |
|---|---|
| `api-architect` | `api-design-report-v1` |
| `backend-developer` | `backend-implementation-v1` |
| `code-archaeologist` | `codebase-assessment-v1` |
| `code-reviewer` | `code-review-v1` |
| `django-api-developer` | `django-api-implementation-v1` |
| `django-backend-expert` | `django-backend-implementation-v1` |
| `django-expert` | `django-fullstack-implementation-v1` |
| `django-orm-expert` | `django-orm-optimization-v1` |
| `documentation-specialist` | `documentation-changelog-v1` |
| `fastapi-expert` | `fastapi-implementation-v1` |
| `frontend-developer` | `frontend-implementation-v1` |
| `laravel-backend-expert` | `laravel-implementation-v1` |
| `laravel-eloquent-expert` | `eloquent-work-summary-v1` |
| `ml-data-expert` | `ml-data-implementation-v1` |
| `performance-optimizer` | `performance-report-v1` |
| `project-analyst` | `stack-analysis-v1` |
| `python-devops-cicd-expert` | `python-deployment-delivery-v1` |
| `python-expert` | `python-implementation-v1` |
| `python-performance-expert` | `python-performance-report-v1` |
| `python-security-expert` | `python-security-assessment-v1` |
| `python-testing-expert` | `python-testing-delivery-v1` |
| `python-web-scraping-expert` | `python-acquisition-report-v1` |
| `rails-activerecord-expert` | `rails-activerecord-optimization-v1` |
| `rails-api-developer` | `rails-api-implementation-v1` |
| `rails-backend-expert` | `rails-backend-implementation-v1` |
| `react-component-architect` | `react-component-delivery-v1` |
| `react-nextjs-expert` | `nextjs-implementation-v1` |
| `tailwind-css-expert` | `component-delivery-v1` |
| `team-configurator` | `team-configuration-v1` |
| `tech-lead-orchestrator` | `route-plan-v1` |
| `vue-component-architect` | `vue-implementation-v1` |
| `vue-nuxt-expert` | `nuxt-implementation-v1` |
| `vue-state-manager` | `vue-state-delivery-v1` |

## Dangling-edge substitutions
- security-guardian -> python-security-expert for Python, otherwise code-reviewer with PROC-16
- refactoring-expert -> matching implementer for the stack
- testing-specialist -> python-testing-expert for Python, otherwise matching implementer
- accessibility-expert -> matching frontend agent with PROC-14
- laravel-api-architect -> api-architect then laravel-backend-expert
- database-architect -> matching ORM agent, otherwise backend-developer

## Two-agent policy
At most two independent agents may run concurrently on VS Code or CLI orchestration surfaces. Cloud stages are sequential separately selected sessions.

## Surface fallbacks
Missing agent, browser, MCP, or web capability must be reported explicitly; never impersonate the next agent or fabricate evidence.
