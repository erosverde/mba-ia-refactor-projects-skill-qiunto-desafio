# Desafio 5 · Skill de auditoria e refatoração arquitetural

A skill `refactor-arch` foi criada para o OpenAI Codex e executada em três APIs legadas. Ela identifica a stack, produz um relatório com evidências e aguarda aprovação antes de editar o código. A execução confirmou o boot dos três projetos e validou **44 combinações de método e caminho** usando bancos SQLite de teste. [Enunciado original](https://github.com/devfullcycle/mba-ia-refactor-projects-skill)

## Análise Manual

A análise manual seguiu o fluxo das rotas até a persistência e a resposta HTTP. Os documentos registram linhas do código original, severidade e impacto. A auditoria da skill foi apresentada para aprovação antes de cada refatoração.

| Projeto | Achados manuais | Exemplos e impacto |
|---|---:|---|
| [code-smells-project](code-smells-project/analise-manual-code-smells-project.md) | 15 | SQL recebido diretamente pela API, senhas expostas e estoque validado por item. Os efeitos incluem leitura ou alteração indevida, exposição de credenciais e saldo negativo. |
| [ecommerce-api-legacy](ecommerce-api-legacy/analise-manual-ecommerce-api-legacy.md) | 5 | Dados de pagamento nos logs, consultas N+1 e matrículas sem referência após exclusão. Os efeitos incluem exposição de dados, custo crescente do relatório e perda do vínculo com o aluno. |
| [task-manager-api](task-manager-api/analise-manual-task-manager-api.md) | 11 | Hashes expostos, operações sem autorização e contagens que carregavam todas as tarefas. Os efeitos incluem exposição de credenciais, alterações indevidas e uso crescente de memória. |

## Construção da Skill

A cópia inicial foi criada em `code-smells-project/.agents/skills/refactor-arch/`. Os outros dois projetos receberam cópias idênticas dos seis arquivos. O [SKILL.md](code-smells-project/.agents/skills/refactor-arch/SKILL.md) coordena análise, auditoria e refatoração com validação.

| Referência | Decisão de design |
|---|---|
| [Análise de projeto](code-smells-project/.agents/skills/refactor-arch/references/analise-de-projeto.md) | Detectar linguagem, framework, banco e domínio por manifestos, imports, inicialização e rotas. |
| [Catálogo de anti-patterns](code-smells-project/.agents/skills/refactor-arch/references/catalogo-de-anti-patterns.md) | Dez padrões com sinais verificáveis, cobrindo acesso a dados, segurança, validação, consistência, separação de responsabilidades e manutenção. O catálogo inclui APIs legadas. |
| [Template de auditoria](code-smells-project/.agents/skills/refactor-arch/references/template-de-auditoria.md) | Agrupar ocorrências com a mesma causa e registrar severidade, linhas, evidência, impacto e correção proposta. |
| [Diretrizes MVC](code-smells-project/.agents/skills/refactor-arch/references/diretrizes-mvc.md) | Definir responsabilidades para models, rotas, controllers e serialização JSON, com serviços para regras e consultas mais complexas. |
| [Playbook de refatoração](code-smells-project/.agents/skills/refactor-arch/references/playbook-de-refatoracao.md) | Dez transformações com exemplos de antes e depois e verificações de regressão. |

Os critérios se aplicam em stacks diferentes. A mesma regra de N+1 encontrou consultas dentro dos laços de callbacks do SQLite no Express e dentro de laços de consultas ORM no Flask. No Task Manager, a solução aproveitou blueprints e models existentes. A detecção de APIs legadas identificou `Query.get()` e `datetime.utcnow()` nesse projeto. Na validação do Express, o npm 8 em diretório temporário permitiu instalar as versões do lockfile.

## Resultados

| Projeto e relatório | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Rotas validadas |
|---|---|---:|---:|---:|---:|---:|---:|
| [code-smells-project](reports/audit-project-1.md) | Python, Flask 3.1.1, SQLite | 6 | 3 | 5 | 1 | 15 | 19/19 |
| [ecommerce-api-legacy](reports/audit-project-2.md) | Node.js, Express 4.22.1, SQLite | 3 | 4 | 3 | 1 | 11 | 3/3 |
| [task-manager-api](reports/audit-project-3.md) | Python, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLite | 2 | 4 | 3 | 2 | 11 | 22/22 |
| **Total** | | **11** | **11** | **11** | **4** | **37** | **44/44** |

### Estrutura antes e depois

| Projeto | Antes | Depois |
|---|---|---|
| `code-smells-project` | Inicialização, registro de rotas e operações administrativas em `app.py`. Conexão SQLite global e consultas misturadas a regras de negócio. | Factory em `app.py`, blueprint em `routes.py`, configuração em `settings.py`, tratamento central de erros e conexão por requisição. |
| `ecommerce-api-legacy` | `AppManager.js` concentrava schema, rotas, SQL, checkout e relatório. | `src/routes/`, `src/controllers/`, `src/services/` e `src/models/`, com configuração externa e checkout transacional. |
| `task-manager-api` | Blueprints acumulavam handlers, regras e agregações. Configuração de debug e segredos no código. | Blueprints declarativos, `controllers/`, serviços de autenticação e indicadores, configuração externa e agregações no SQLite. |

### Checklist de validação

| Verificação | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Stack, domínio e escopo registrados | ✓ 4 fontes Python | ✓ 3 fontes JavaScript | ✓ 15 fontes Python |
| Relatório com linhas e severidades, seguido de aprovação | ✓ 15 achados | ✓ 11 achados | ✓ 11 achados |
| Estrutura MVC, configuração e tratamento de erros | ✓ Blueprint, controllers e models | ✓ Router, controllers, serviços e store | ✓ Blueprints, controllers, models e serviços |
| Boot real em localhost | ✓ `GET /health` → 200 | ✓ Relatório sem credencial → 401 esperado | ✓ `GET /health` → 200 |
| Endpoints originais com SQLite de teste | ✓ 19/19, banco temporário | ✓ 3/3, banco em memória | ✓ 22/22, banco temporário |
| Regressões verificadas | ✓ Estoque, hash de senha, histórico, bloqueio administrativo | ✓ Checkout recusado sem gravação, autorização e histórico financeiro | ✓ Propriedade de recursos, expiração, revogação, atualização de hash e quatro respostas de indicadores equivalentes |

### Evidências de execução

Trechos das saídas dos testes locais, na ordem dos projetos da tabela:

```text
PASS boot python app.py; GET /health 200
PASS 19/19; estoque, hash, bloqueio HTTP e CLI local

PASS boot do ponto de entrada src/app.js e resposta HTTP 401 esperada
PASS 3/3 routes; authentication, declined checkout, and financial history

PASS boot python app.py; GET /health 200
PASS 22/22, 4 indicadores equivalentes, autorização e migração de hash
```

No primeiro projeto, as duas rotas administrativas continuam registradas e respondem `403` por design. Contas legadas que ainda têm senhas em texto claro precisam de redefinição local. A limpeza automática em lote ficou pendente. O cálculo de vendas foi preservado até a definição de quais status representam vendas efetivadas. No Express, o checkout simulado exige modo de teste e a instalação registrou avisos de depreciação de dependências transitivas. No Task Manager, a comparação dos indicadores excluiu os timestamps gerados em cada execução.

## Como Executar

Abra uma sessão do Codex em uma das pastas dos projetos. No CLI, execute o par de comandos correspondente a partir da raiz do repositório:

| Projeto | Pasta e comando | Prompt no Codex |
|---|---|---|
| `code-smells-project` | `cd code-smells-project`, depois `codex` | `Use $refactor-arch neste projeto e apresente o relatório da fase 2.` |
| `ecommerce-api-legacy` | `cd ecommerce-api-legacy`, depois `codex` | `Use $refactor-arch neste projeto e apresente o relatório da fase 2.` |
| `task-manager-api` | `cd task-manager-api`, depois `codex` | `Use $refactor-arch neste projeto e apresente o relatório da fase 2.` |

Esses comandos auditam a revisão aberta. Para reproduzir os relatórios do código original, use como referência as revisões `bce5efb` para a loja Flask, `b256bc8` para a API Express e `ac3322e` para o Task Manager. As duas últimas revisões têm o código original do projeto correspondente e a skill no primeiro projeto.

Para validar as aplicações refatoradas, instale as dependências dentro da pasta do projeto e execute o ponto de entrada. Use um banco descartável e siga as instruções de configuração de cada API.

| Projeto | Instalação e boot | Validação |
|---|---|---|
| [code-smells-project](code-smells-project/README.md) | `python -m pip install -r requirements.txt` e `python app.py` | Configure `LOJA_DB` para um arquivo temporário. Confira o health check, os fluxos de catálogo, login e pedidos e o bloqueio das rotas administrativas. |
| [ecommerce-api-legacy](ecommerce-api-legacy/README.md) | `npm ci` com npm compatível com o lockfile e `npm start` | Use [api.http](ecommerce-api-legacy/api.http) com credencial administrativa local. Para checkout simulado, configure `NODE_ENV=test` e `PAYMENT_MODE=test`. O SQLite já roda em memória. |
| [task-manager-api](task-manager-api/README.md) | `python -m pip install -r requirements.txt` e `python app.py` | Configure `TASK_DATABASE_URI` para um SQLite temporário. Prepare contas de teste, faça login e compare as respostas com token de administrador, token de conta comum e credencial ausente. |
