from database import get_db
from werkzeug.security import check_password_hash, generate_password_hash

def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    result = []
    for row in rows:

        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        })
    return result

def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        }
    return None

def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid

def atualizar_produto(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, id),
        )

def deletar_produto(id):
    db = get_db()
    with db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (id,)).fetchone():
            db.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (id,))
        else:
            db.execute("DELETE FROM produtos WHERE id = ?", (id,))

def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        })
    return result

def get_usuario_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        }
    return None

def login_usuario(email, senha):
    db = get_db()
    row = db.execute("SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not row["senha"]:
        return None
    # Legacy plaintext credentials require a password reset outside the login flow.
    if not row["senha"].startswith(("scrypt:", "pbkdf2:")) or not check_password_hash(row["senha"], senha):
        return None
    return {campo: row[campo] for campo in ("id", "nome", "email", "tipo")}

def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid

def criar_pedido(usuario_id, itens):
    if type(usuario_id) is not int or usuario_id < 1 or not isinstance(itens, list):
        return {"erro": "Usuário ou itens inválidos"}
    quantidades = {}
    for item in itens:
        if not isinstance(item, dict):
            return {"erro": "Item inválido"}
        produto_id, quantidade = item.get("produto_id"), item.get("quantidade")
        if type(produto_id) is not int or type(quantidade) is not int or min(produto_id, quantidade) < 1:
            return {"erro": "Produto e quantidade devem ser inteiros positivos"}
        quantidades[produto_id] = quantidades.get(produto_id, 0) + quantidade

    db = get_db()
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            produtos = {}
            for produto_id, quantidade in quantidades.items():
                produto = db.execute("SELECT preco, estoque FROM produtos WHERE id = ? AND ativo = 1", (produto_id,)).fetchone()
                if produto is None or produto["estoque"] < quantidade:
                    raise ValueError("Produto indisponível ou estoque insuficiente")
                produtos[produto_id] = produto["preco"]
            total = sum(produtos[id] * quantidade for id, quantidade in quantidades.items())
            pedido = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            ).lastrowid
            for produto_id, quantidade in quantidades.items():
                baixa = db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (quantidade, produto_id, quantidade),
                )
                if baixa.rowcount != 1:
                    raise ValueError("Estoque insuficiente")
            db.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido, item["produto_id"], item["quantidade"], produtos[item["produto_id"]]) for item in itens],
            )
    except ValueError as error:
        return {"erro": str(error)}
    return {"pedido_id": pedido, "total": total}

def get_pedidos_usuario(usuario_id):
    return _listar_pedidos(usuario_id)

def get_todos_pedidos():
    return _listar_pedidos()

def _listar_pedidos(usuario_id=None):
    sql = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
               produto.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos produto ON produto.id = i.produto_id
    """
    params = ()
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        params = (usuario_id,)
    pedidos = {}
    for row in get_db().execute(sql + " ORDER BY p.id, i.id", params):
        if row["id"] not in pedidos:
            pedidos[row["id"]] = {campo: row[campo] for campo in ("id", "usuario_id", "status", "total", "criado_em")}
            pedidos[row["id"]]["itens"] = []
        if row["item_id"] is not None:
            item = {campo: row[campo] for campo in ("produto_id", "quantidade", "preco_unitario")}
            item["produto_nome"] = row["produto_nome"] if row["produto_nome"] is not None else "Desconhecido"
            pedidos[row["id"]]["itens"].append(item)
    return list(pedidos.values())

def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    if faturamento is None:
        faturamento = 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }

def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    with db:
        return db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)).rowcount == 1

def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()

    clauses = []
    params = []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%"] * 2)
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    for limite, operador in ((preco_min, ">="), (preco_max, "<=")):
        if limite is not None:
            clauses.append(f"preco {operador} ?")
            params.append(limite)
    query = "SELECT * FROM produtos"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    result = []
    for row in rows:

        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        })
    return result
