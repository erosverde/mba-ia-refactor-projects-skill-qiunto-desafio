# Playbook de refatoração

Os pares abaixo são trechos ilustrativos. Adapte nomes, sintaxe e APIs à stack detectada.

| Padrão | Antes | Depois | Verificação |
|---|---|---|---|
| Parametrizar consulta | `cursor.execute(sql_prefix + email)` | `cursor.execute("SELECT id FROM users WHERE email = ?", (email,))` | Buscar um e-mail válido e preservar texto com apóstrofo como dado. |
| Selecionar campos públicos | `jsonify(user.to_dict())` | `jsonify({"id": user.id, "name": user.name})` | Conferir campos públicos e ausência de credenciais. |
| Restringir mutação | `deleteUser(req.params.id)` | `requirePermission(actor, "users:delete"); deleteUser(id)` | Conferir acesso permitido e bloqueio de usuário sem permissão. |
| Externalizar segredo | `app.config["SECRET_KEY"] = "fixture"` | `app.config["SECRET_KEY"] = os.environ["APP_SECRET_KEY"]` | Iniciar com configuração de teste e confirmar diagnóstico claro se faltar. |
| Separar HTTP de regra de negócio | `def checkout(): ... # calcula preço e grava dados` | `def checkout(): return render(checkout_service.run(parse_request()))` | Verificar regra isoladamente e checar resposta HTTP. |
| Agrupar N+1 | `for order in orders: order.items = load_items(order.id)` | `items_by_order = load_items_for_orders(order_ids)` | Comparar conteúdo e contagem de consultas. |
| Validar tipo na fronteira | `priority = int(request.args["priority"])` | `priority = parse_priority(request.args.get("priority"))` | Traduzir falha de parsing em 400 e verificar limites válidos. |
| Tornar escritas atômicas | `create_order(); commit(); reserve_stock(); commit()` | `with transaction(): create_order(); reserve_stock()` | Simular falha na reserva e verificar reversão do pedido. |
| Atualizar API legada | `User.query.get(user_id)` | `db.session.get(User, user_id)` | Confirmar suporte na versão instalada e verificar casos encontrado e ausente. |
| Centralizar constante | `{"version": "1.0"}` repetido em duas rotas | `{"version": settings.api_version}` | Verificar que ambas as rotas refletem a mesma configuração. |

Execute validações de regressão com dados locais. Para autenticação e autorização, confira o comportamento esperado com identidades de teste e verifique que operações negadas não alteram o estado.
