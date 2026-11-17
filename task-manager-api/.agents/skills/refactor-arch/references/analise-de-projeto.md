# Análise de projeto

- Identifique a raiz e leia manifestos e lockfiles. Confirme linguagem e framework pelos imports e pelo ponto de entrada. Registre versões declaradas e resolvidas quando disponíveis.
- Confirme o banco pela configuração, driver ou ORM. Localize schema, migrations, seeds e ciclo de vida da conexão.
- Determine o domínio a partir das entidades e rotas. Inclua registros indiretos, como blueprints e routers, e anote método, caminho e handler.
- Siga fluxos representativos de HTTP até a persistência. Identifique onde ficam parsing, validação, regras, autorização, acesso a dados e serialização.
- Registre os arquivos efetivamente lidos e o que foi excluído do escopo. Ignore dependências vendorizadas, código gerado e ambientes virtuais na contagem de código próprio.
- Use Flask e Express como exemplos de mecanismos de roteamento. Aplique os mesmos critérios de responsabilidade a outras stacks e marque qualquer identificação incerta.
