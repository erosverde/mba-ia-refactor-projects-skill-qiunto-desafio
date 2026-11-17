# Catálogo de anti-patterns

Escolha a severidade pelo impacto demonstrável. Use CRITICAL para exposição grave ou corrupção relevante, HIGH para violações fortes de segurança ou arquitetura, MEDIUM para erros de contrato ou custo relevante e LOW para manutenção localizada. Registre precondições e evite certificar impactos que dependam de configuração desconhecida.

| Padrão | Sinal observável | Severidade inicial |
|---|---|---|
| SQL montado por concatenação | Entrada externa incorporada no comando recebido pelo driver. Confira conversões e origem do dado. | CRITICAL quando há leitura ou escrita indevida relevante |
| Dados sensíveis em respostas ou logs | Senha, hash, chave ou dado de pagamento chega à serialização ou ao logger. Registre o campo sem copiar o valor. | CRITICAL para credenciais ou dados sensíveis acessíveis |
| Operação sem autorização | Alteração por ID sem checagem efetiva de identidade e permissão. Confira middleware e regras globais. | HIGH; CRITICAL se permite controle ou perda ampla de dados |
| Segredo embutido no código | Valor literal usado como chave ou credencial. Distingua configuração ativa de fixture. | HIGH |
| Controller com múltiplas responsabilidades | Handler concentra regras de negócio, consultas diretas e serialização. | HIGH |
| Consultas N+1 | Operação de leitura dentro do laço sobre resultados de outra consulta. Considere cache e carregamento do ORM. | MEDIUM |
| Validação insuficiente na fronteira HTTP | Conversão sem tratamento ou tipo inválido propagado ao banco. | MEDIUM |
| Escrita sem garantia de consistência | Múltiplas gravações relacionadas sem transação ou sem verificação de invariantes. | HIGH |
| API obsoleta | API identificada como deprecated ou legacy na documentação oficial da versão aplicável. Registre versão, fonte e equivalente moderno. | LOW; MEDIUM se compromete atualização prevista |
| Constante duplicada | Mesmo valor de configuração mantido em dois pontos que podem divergir. | LOW |
