# Auditoria — ecommerce-api-legacy

## Escopo

JavaScript em Node.js, Express 4.22.1 e sqlite3 5.1.7 conforme lockfile. Banco SQLite em memória. API de cursos, checkout, matrículas e relatório financeiro. Foram lidos três arquivos JavaScript, o manifesto e o lockfile. As três rotas estavam concentradas em src/AppManager.js, junto do esquema, das consultas e das regras de negócio.

## Achados

11 achados únicos — 3 CRITICAL, 4 HIGH, 3 MEDIUM e 1 LOW. Evidência por leitura estática do código original.

| ID | Achado | Arquivo e linhas | Severidade | Evidência e impacto | Correção proposta |
|---|---|---|---|---|---|
| E01 | Cartão e chave do gateway em logs | src/AppManager.js:45 | CRITICAL | Ambos os valores são registrados antes da decisão do pagamento. Dados reais e chaves ativas poderiam chegar a quem acessa os logs. | Remover os valores dos logs e rotacionar a chave se ativa. |
| E02 | Relatório e exclusão sem autorização | src/app.js:5–10, src/AppManager.js:80, 131–135 | CRITICAL | Sem controle externo, clientes podem consultar dados financeiros e remover contas. | Exigir credencial administrativa. |
| E03 | Pagamento aprovado pelo prefixo do cartão | src/AppManager.js:45–54 | CRITICAL | Uma execução real poderia gravar PAID e liberar matrícula sem cobrança. | Isolar simulador em teste e rejeitar pagamento sem provedor. |
| E04 | Credenciais literais | src/utils.js:1–6 | HIGH | Senha de banco e chave do gateway estão no código. | Remover configuração ociosa e carregar credenciais necessárias pelo ambiente. |
| E05 | Proteção fraca de senhas | src/utils.js:17–22, src/AppManager.js:18, 67–69 | HIGH | Há senha padrão, valor literal no seed e derivação de um prefixo Base64 curto. | Exigir senha no cadastro e usar hash adaptativo com salt. |
| E06 | Checkout reutiliza conta sem comprovar identidade | src/AppManager.js:40–43, 66–75 | HIGH | A matrícula pode ser atribuída à conta de outra pessoa. | Verificar a senha antes de vincular a matrícula. |
| E07 | Checkout pode gravar estado parcial | src/AppManager.js:46–60, 66–71 | HIGH | Recusa ou falha pode deixar usuário ou matrícula gravados. Erro de auditoria é ignorado. | Agrupar usuário, matrícula, pagamento e evento em uma transação. |
| E08 | N+1 no relatório | src/AppManager.js:83, 92, 104, 106 | MEDIUM | Uma consulta inicial, uma por curso e duas por matrícula. | Consultar em lote. |
| E09 | Exclusão rompe referência de matrícula | src/AppManager.js:14–15, 104–114, 131–135 | MEDIUM | A matrícula perde o vínculo com o usuário e pode exibir Unknown. | Anonimizar a conta e preservar o histórico. |
| E10 | Callbacks ignoram erros | src/AppManager.js:92–93, 104–114, 133–135 | MEDIUM | Falhas podem interromper a resposta ou produzir sucesso indevido. | Propagar erros e verificar linhas alteradas. |
| E11 | Cache global sem expiração | src/utils.js:9–14, src/AppManager.js:59 | LOW | Acumula uma entrada por usuário que conclui o checkout. | Remover cache sem leitores. |

E01, E08 e E09 também constam da análise manual. Nenhuma API obsoleta foi confirmada no escopo.

## Plano aprovado

Separar rotas, controllers, serviços e persistência. Preservar os três métodos e caminhos. Autorizar as duas operações administrativas, verificar a identidade quando houver uma conta existente, responder 404 na exclusão de conta ausente e habilitar o simulador apenas no modo de teste. Preservar o total de pagamentos PAID após anonimizar uma conta.

## Validação após a refatoração

O ponto de entrada src/app.js iniciou em localhost. Os testes HTTP abriram instâncias locais com bancos SQLite em memória separados para o modo de teste e para o modo sem simulador.

| Rota | Resultado observado |
|---|---|
| POST /api/checkout | 200 na simulação aprovada, 400 na recusa, 401 para senha incorreta de conta existente, 404 para curso ausente e 503 fora do modo de teste. |
| GET /api/admin/financial-report | 200 com credencial administrativa, 401 sem credencial e 403 com credencial inválida. |
| DELETE /api/users/:id | 200 com credencial e conta ativa, 400 para ID inválido, 401 sem credencial, 403 com credencial inválida e 404 para conta inexistente ou já excluída. |

O checkout recusado deixou o relatório intacto. Um checkout posterior para o mesmo e-mail aceitou uma senha diferente no cadastro, confirmando que a recusa anterior também não deixou uma conta criada. Após a exclusão, o nome do aluno passou a ser Unknown e os dois pagamentos de 497 continuaram somando 994 para o curso. O curso de exemplo preservou a receita inicial de 997.

A instalação do lockfile foi feita em diretório temporário usando npm 8. A instalação emitiu avisos de depreciação sobre dependências transitivas.
