# Análise manual — `ecommerce-api-legacy`

A tabela reúne **5 achados** identificados por leitura do código. O cartão e a chave do gateway aparecem no mesmo registro porque são expostos pela mesma chamada de log. Os impactos foram avaliados por análise estática.

| Achado | Arquivo | Linha | Severidade | Impacto |
|---|---|---|---|---|
| Dados de cartão e chave do gateway expostos no log de `POST /api/checkout` | `src/AppManager.js` | 45 | `CRITICAL` | Se forem usados dados reais ou uma chave ativa, quem tiver acesso aos logs pode obter esses valores. O registro ocorre antes da decisão do pagamento, inclusive em tentativas recusadas. |
| Consultas N+1 em dois níveis no relatório financeiro | `src/AppManager.js` | 83, 92, 104 e 106 | `MEDIUM` | A rota executa uma consulta inicial, uma por curso e duas por matrícula. Com 10 cursos e 100 matrículas, são 211 consultas, o que pode elevar a latência do relatório. |
| Exclusão de usuário deixa matrículas sem referência | `src/AppManager.js` | 14–15 e 131–135 | `MEDIUM` | As matrículas continuam apontando para o usuário excluído. O relatório pode mostrar o aluno como `"Unknown"`, enquanto o pagamento vinculado à matrícula ainda compõe a receita se estiver com status `PAID`. |
| Callback do checkout usa nomes pouco descritivos | `src/AppManager.js` | 29–33, 37–40 | `LOW` | Abreviações como `u`, `e`, `p`, `cid` e `cc` dificultam seguir dados do corpo da requisição entre os callbacks. |
| Contador de receita sem uso | `src/utils.js` e `src/AppManager.js` | `utils.js:10, 25` e `AppManager.js:2, 108–109` | `LOW` | `totalRevenue` é exportado e importado, mas a receita é calculada em outro campo. O estado morto induz leitores a procurar uma atualização que não existe. |

**Total: 5 achados** — 1 `CRITICAL`, 2 `MEDIUM` e 2 `LOW`.
