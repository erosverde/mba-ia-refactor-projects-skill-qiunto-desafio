# Auditoria — code-smells-project

## Escopo

Código original na revisão bce5efb. Python, Flask 3.1.1, Flask-CORS 5.0.1 e SQLite. API de catálogo, usuários, pedidos e estoque. Foram lidos quatro arquivos Python e requirements.txt. A aplicação declara 19 rotas.

## Achados

15 achados únicos — 6 CRITICAL, 3 HIGH, 5 MEDIUM e 1 LOW. Evidência por leitura estática.

| ID | Achado | Arquivo e linhas | Severidade | Evidência e impacto | Correção proposta |
|---|---|---|---|---|---|
| A01 | SQL arbitrário pela API | app.py:59–76 | CRITICAL | Entrada chega diretamente ao driver e pode afetar os dados acessíveis à conexão. | Desativar SQL livre via HTTP. |
| A02 | Reset sem autorização | app.py:47–55 | CRITICAL | Quatro tabelas são apagadas sem verificação de permissão. | Restringir reset à manutenção local. |
| A03 | SQL construído com entrada externa | models.py:47–50, 57–61, 109–111, 126–129, 139–166, 289–299 | CRITICAL | Concatenação pode comprometer autenticação, consultas e gravações. | Parametrizar e validar tipos. |
| A04 | Senhas em texto claro | models.py:126–130, database.py:75–84 | CRITICAL | Cadastro e seed permitem recuperação direta de senhas do banco. | Usar hash e redefinir senhas legadas. |
| A05 | Senhas em respostas de usuários | models.py:83, 99, controllers.py:132, 140 | CRITICAL | Senhas chegam ao cliente. | Selecionar campos públicos. |
| A06 | Chave secreta fixa e exposta | app.py:7, controllers.py:285–289 | CRITICAL | A resposta divulga um valor que pode comprometer a integridade de dados assinados. | Externalizar, remover da resposta e rotacionar se ativa. |
| A07 | Conexão global compartilhada | database.py:4–11 | HIGH | Escritas podem interferir em transações concorrentes. | Usar conexão por requisição. |
| A08 | Estoque validado por item | models.py:139–146, 163–168 | HIGH | Quantidade acumulada pode exceder o saldo. | Consolidar quantidades e reservar atomicamente. |
| A09 | Debug na rede | app.py:80–88 | HIGH | Erros podem expor detalhes internos. | Desativar debug e configurar escuta. |
| A10 | N+1 na listagem de pedidos | models.py:174, 188, 192, 206, 220, 224 | MEDIUM | Cada pedido e cada item adicionam leituras. | Carregar com consulta em lote. |
| A11 | Status confirma pedido inexistente | models.py:279–283, controllers.py:245, 252 | MEDIUM | A API pode confirmar alteração sem linhas afetadas. | Verificar resultado e responder 404. |
| A12 | Indicadores incluem todos os status | models.py:239–243, 256–272 | MEDIUM | A interpretação como vendas efetivadas pode distorcer faturamento e ticket médio. | Preservar o cálculo até confirmar a regra. |
| A13 | Exceções internas em respostas | app.py:78, controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292 | MEDIUM | Mensagens podem divulgar detalhes internos. | Centralizar erros. |
| A14 | Exclusão rompe histórico | database.py:45–53, models.py:68–69, 192–196, 224–228 | MEDIUM | Itens podem perder o nome do produto vendido. | Desativar produtos vendidos e proteger a referência. |
| A15 | Versão duplicada | app.py:36, controllers.py:285 | LOW | Respostas podem divulgar versões divergentes. | Centralizar configuração. |

## Plano aprovado

Separar roteamento, configuração, controllers e persistência. Preservar os 19 caminhos e métodos, responder 403 nas duas operações administrativas via HTTP, remover campos sensíveis e responder 404 quando o pedido não existir na atualização de status. Validar boot e endpoints em SQLite temporário.

## Validação após a refatoração

- Boot real com python app.py em localhost e SQLite temporário. GET /health retornou 200.
- Cliente de testes do Flask cobriu todas as 19 combinações de método e rota. Foram 14 respostas 200, 3 respostas 201 e 2 respostas 403 esperadas.
- Casos adicionais verificaram 400 para filtro inválido, estoque inválido, quantidade acima do saldo e status inválido, 401 para senha incorreta e 404 para pedido inexistente.
- Asserções no SQLite verificaram o hash da senha, a redução de estoque, a ausência de gravação no pedido rejeitado, a preservação do histórico após desativar o produto e a ausência de alterações pelas rotas administrativas.
- Os comandos locais reset-password e reset-db passaram no banco temporário.

## Revalidação na PR #1

As 19 rotas passaram novamente com SQLite temporário. O teste versionado em code-smells-project/tests/test_email_registration.py cobre cadastro concorrente (201 e 409), autenticação de duplicatas legadas com senhas distintas e rejeição de login ambíguo até a redefinição local de uma conta pelo ID.
