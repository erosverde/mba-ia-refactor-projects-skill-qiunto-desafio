---
name: refactor-arch
description: Audita a arquitetura de aplicações, registra achados com evidências e, após aprovação, refatora para MVC e valida os endpoints existentes.
---

# Refactor Arch

Trabalhe no projeto indicado. Use as evidências do código atual e mantenha o escopo dentro desse projeto.

1. **Análise.** Leia [análise de projeto](references/analise-de-projeto.md). Apresente linguagem, framework, banco, domínio, arquitetura, rotas e quantidade de arquivos analisados.
2. **Auditoria.** Use o [catálogo](references/catalogo-de-anti-patterns.md) e o [template](references/template-de-auditoria.md). Faça revisão defensiva por leitura do código e proponha correções. Apresente o relatório na conversa e peça aprovação explícita para o escopo de mudanças. Encerre a etapa nesse ponto. As fases 1 e 2 são somente leitura.
3. **Refatoração e validação.** Após aprovação, preserve o relatório com as referências do código original, registre o comportamento inicial e aplique as mudanças aprovadas conforme as [diretrizes MVC](references/diretrizes-mvc.md) e o [playbook](references/playbook-de-refatoracao.md). Use dados de teste locais para validar o boot e os contratos dos endpoints, incluindo erros esperados. Compare a estrutura antes e depois e informe comandos, resultados e verificações pendentes.

Use as análises manuais existentes como comparação depois de produzir o relatório independente. Para a entrega do desafio, guarde a auditoria em `reports/audit-project-{1,2,3}.md` na raiz do repositório, conforme o projeto e após autorização de escrita.
