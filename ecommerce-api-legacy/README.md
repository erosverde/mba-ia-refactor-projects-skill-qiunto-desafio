# ecommerce-api-legacy

API de cursos com Express e SQLite em memória. O banco é recriado a cada inicialização.

## Como rodar

Use um Node.js com suporte a scrypt e uma versão do npm compatível com o lockfile.

```sh
npm ci
npm start
```

Por padrão, o servidor escuta em `127.0.0.1:3000`. Para configurar o endereço e a porta, defina `HOST` e `PORT`.

Defina `ADMIN_API_TOKEN` com um valor aleatório antes de testar o relatório e a exclusão. Envie esse valor no cabeçalho `Authorization: Bearer <token>`. A conta de exemplo existe para preservar o histórico financeiro inicial e não tem senha de checkout.

Para validar o checkout com dados fictícios, defina `NODE_ENV=test` e `PAYMENT_MODE=test` antes de iniciar a API. Fora desse modo, o checkout responde 503 porque não há integração de pagamento real.
