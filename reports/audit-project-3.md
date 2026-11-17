# Auditoria — task-manager-api

## Escopo

Revisão original ac3322e. Python, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0 e SQLite. API de tarefas, usuários, categorias e relatórios. Escopo de 15 arquivos Python e requirements.txt, com 22 rotas declaradas.

## Achados

11 achados únicos — 2 CRITICAL, 4 HIGH, 3 MEDIUM e 2 LOW. Evidência por leitura estática.

| ID | Achado | Arquivo e linhas | Severidade | Evidência e impacto | Correção proposta |
|---|---|---|---|---|---|
| T01 | Hash em respostas HTTP | models/user.py:16–25; routes/user_routes.py:33–40, 85–86, 129, 209 | CRITICAL | O hash sai em consulta, cadastro, atualização e login, permitindo tentativas de recuperação da senha. | Serializar somente campos públicos. |
| T02 | Recursos sem autorização | app.py:15–20; routes/user_routes.py:93–129, 135–146; routes/task_routes.py:157–233; routes/report_routes.py:191–219 | CRITICAL | Alterações e exclusões, inclusive de senha e papel, ficam acessíveis sem verificação na aplicação. | Verificar identidade, papel e propriedade. |
| T03 | Senhas com MD5 sem salt | models/user.py:27–32 | HIGH | Hashes iguais para senhas iguais e baixo custo de comparação. | Usar hash adaptativo e migrar após autenticação válida. |
| T04 | Depuração habilitada na rede | app.py:33–34 | HIGH | Debug em todas as interfaces pode divulgar detalhes internos. | Desativar debug e configurar endereço externamente. |
| T05 | Segredos no código | app.py:13; services/notification_service.py:10, 17 | HIGH | Chave Flask e credencial SMTP literais. | Externalizar e rotacionar valores ativos. |
| T06 | Token de login previsível | routes/user_routes.py:197–210 | HIGH | O valor deriva do ID, sem assinatura ou prova de identidade. | Emitir e verificar token assinado com expiração. |
| T07 | Consultas N+1 | routes/task_routes.py:14–51; routes/report_routes.py:53–56, 159–163 | MEDIUM | Consultas em laços aumentam o trabalho com o volume. | Carregar em lote e agrupar no banco. |
| T08 | Filtros numéricos inválidos podem causar 500 | routes/task_routes.py:261, 264 | MEDIUM | Conversão sem tratamento de erro. | Validar e devolver 400. |
| T09 | Estatísticas carregam todas as tarefas | routes/task_routes.py:275–286; routes/report_routes.py:15–36 | MEDIUM | Transfere a tabela para contar atrasos em Python. | Filtrar e agregar no SQLite. |
| T10 | Consulta por chave primária usa Query.get | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | LOW | API legada do SQLAlchemy. | Usar Session.get. |
| T11 | Uso de datetime.utcnow | models/task.py:15–16, 52; models/user.py:14; models/category.py:11; routes/report_routes.py:35, 42, 45, 71, 133; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; seed.py:66–74; services/notification_service.py:35; utils/helpers.py:38 | LOW | API depreciada no Python 3.12. | Obter horário UTC moderno e preservar a representação SQLite existente. |

Referências para APIs legadas: [SQLAlchemy Query.get](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#orm-query-get-method-moves-to-session) e [Python datetime.utcnow](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow).

## Plano aprovado

Preservar os blueprints e as 22 rotas. Manter a raiz, o health check, o login e o cadastro de contas comuns públicos. Exigir autenticação nas demais operações, limitar o acesso de usuários comuns aos próprios recursos e reservar administração e relatório global ao papel admin. Comparar indicadores com os resultados originais usando uma fixture equivalente em SQLite temporário.

## Validação após a refatoração

- O servidor iniciou com python app.py em localhost e GET /health respondeu 200 usando um SQLite temporário.
- O cliente de testes do Flask verificou as mesmas 22 combinações de método e caminho registradas na versão original. Foram 19 respostas 200 e 3 respostas 201 nos fluxos autorizados.
- Os testes adicionais verificaram 400 para filtros inválidos, 401 para credencial ausente, adulterada, expirada ou revogada e 403 para operações fora do papel ou da propriedade da conta.
- O login válido migrou os hashes da fixture de MD5 para scrypt. Consulta individual, cadastro, atualização e login omitiram o campo password.
- Os resultados de /tasks/stats, /reports/summary, /reports/user/<id> e /categories foram equivalentes aos da versão original para o administrador e a mesma fixture. Timestamps gerados separadamente foram excluídos da comparação.
- A listagem GET /tasks executou duas consultas SELECT no teste, incluindo a leitura da conta autenticada.
