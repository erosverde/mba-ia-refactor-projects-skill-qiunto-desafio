# Análise manual — `task-manager-api`

A tabela reúne **9 achados** identificados por leitura estática. As ocorrências repetidas aparecem na mesma linha, com as respectivas referências. Os caminhos são relativos à pasta do projeto.

| Achado | Arquivo | Linha | Severidade | Impacto |
|---|---|---|---|---|
| Hash de senha incluído nas respostas de consulta individual, cadastro, atualização e login | `models/user.py`, `routes/user_routes.py` | `user.py:16–25` e `user_routes.py:33–40, 85–86, 129, 209` | `CRITICAL` | Quem tiver acesso à consulta individual pode receber o hash da conta. O valor também circula nas demais respostas, aumentando os pontos de exposição. |
| Operações sobre recursos sem verificação de autorização na aplicação | `app.py`, `routes/user_routes.py`, `routes/task_routes.py`, `routes/report_routes.py` | `app.py:15–20`, `user_routes.py:93–129, 135–146`, `task_routes.py:157–220, 226–233`, `report_routes.py:191–219` | `CRITICAL` | Sem um controle externo, quem alcançar a API pode alterar ou excluir recursos. Na atualização de usuário, a requisição também pode alterar a senha e o papel da conta indicada. |
| Senhas protegidas com MD5 sem salt | `models/user.py` | 27–32 | `HIGH` | Se os hashes forem expostos, a comparação rápida facilita tentativas de recuperação de senhas. Contas com a mesma senha produzem o mesmo hash. |
| Modo de depuração ativado no servidor acessível pela rede | `app.py` | 33–34 | `HIGH` | Ao iniciar a aplicação por esse ponto de entrada, o Flask escuta em todas as interfaces com `debug=True`. Falhas podem expor detalhes internos a quem alcançar o servidor. |
| Segredos definidos diretamente no código | `app.py`, `services/notification_service.py` | `app.py:13` e `notification_service.py:10, 17` | `HIGH` | Quem acessar o código pode obter a chave do Flask e a senha configurada para SMTP. O impacto depende de esses valores estarem ativos e de quais serviços os utilizam. |
| Login devolve um token previsível sem assinatura | `routes/user_routes.py` | 209–210 | `HIGH` | O valor retornado deriva do ID do usuário e não comprova identidade. Se um consumidor passar a confiar nele como credencial, a identidade associada ao token pode ser falsificada. |
| Consultas N+1 na listagem de tarefas, no resumo e nas categorias | `routes/task_routes.py`, `routes/report_routes.py` | `task_routes.py:14–51` e `report_routes.py:53–56, 159–163` | `MEDIUM` | A listagem busca usuários e categorias dentro do laço de tarefas, com consultas efetivas condicionadas ao cache da sessão. O resumo consulta tarefas por usuário e a listagem conta tarefas por categoria, elevando o custo conforme os dados crescem. |
| Filtros numéricos da busca convertidos sem tratar valores inválidos | `routes/task_routes.py` | 261, 264 | `MEDIUM` | Um valor não numérico em `priority` ou `user_id` pode causar uma exceção e resultar em `500`, dificultando que o cliente identifique e corrija o filtro. |
| Estatísticas carregam todas as tarefas para calcular atrasos | `routes/task_routes.py`, `routes/report_routes.py` | `task_routes.py:275–286` e `report_routes.py:15–36` | `MEDIUM` | As duas rotas fazem várias contagens e carregam a tabela de tarefas para avaliar atrasos em Python. O volume transferido do SQLite e o uso de memória crescem com o tamanho da tabela. |

**Total: 9 achados** — 2 `CRITICAL`, 4 `HIGH` e 3 `MEDIUM`.
