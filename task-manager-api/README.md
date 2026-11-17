# task-manager-api

API de tarefas, usuários, categorias e relatórios em Python/Flask com SQLite.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

O servidor escuta em localhost na porta 5000 por padrão. Configure `TASK_HOST`, `TASK_PORT` e `TASK_DATABASE_URI` pelo ambiente para alterar esses valores. Para que os tokens continuem válidos entre reinícios ou em múltiplos processos, defina o mesmo `TASK_SECRET_KEY` aleatório em todas as instâncias. Sem essa variável, cada instância gera sua própria chave.

Para carregar os dados de demonstração, aponte `TASK_DATABASE_URI` para um banco descartável, defina `TASK_SEED_PASSWORD` com oito caracteres ou mais e execute `python seed.py`. O seed substitui as tarefas, contas e categorias do banco selecionado. A conta de exemplo `joao@email.com` tem papel admin.

## Acesso à API

As rotas de raiz, saúde, login e cadastro de contas comuns são públicas. Envie o token devolvido por `POST /login` como `Authorization: Bearer <token>` nas demais rotas. O token expira em uma hora e deixa de ser aceito após mudança de senha ou desativação da conta. Contas comuns acessam o próprio perfil, suas tarefas e o relatório individual. Administradores podem gerenciar contas e categorias e consultar o relatório global.

Após um login válido, a API substitui o hash MD5 legado por scrypt. As respostas de usuário omitem o hash. As configurações SMTP opcionais são `TASK_SMTP_HOST`, `TASK_SMTP_PORT`, `TASK_SMTP_USER` e `TASK_SMTP_PASSWORD`.
