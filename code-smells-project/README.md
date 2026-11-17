# code-smells-project

API de e-commerce em Python/Flask usada no desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A API roda em `http://127.0.0.1:5000` por padrão. Configure `LOJA_HOST`, `LOJA_PORT`, `LOJA_DB` ou `LOJA_SECRET_KEY` pelo ambiente quando necessário. O SQLite inicializa o esquema e os produtos de exemplo. Crie uma conta pela rota `POST /usuarios` para testar o login.

## Manutenção local

As rotas administrativas HTTP respondem 403. A partir da pasta do projeto, use:

```bash
python -m flask --app app reset-password usuario@example.test
python -m flask --app app reset-db
```

Novos cadastros com e-mail já existente recebem 409. Para contas legadas com o mesmo e-mail, o login exige que a senha identifique uma única conta. Use `python -m flask --app app reset-password usuario@example.test --user-id 42` para redefinir uma conta específica sem alterar as outras.

Contas legadas com senha em texto claro exigem redefinição local para voltar a autenticar. O comando de reset do banco solicita confirmação e apaga os dados da loja. Confira o arquivo apontado por `LOJA_DB` antes de executar.
