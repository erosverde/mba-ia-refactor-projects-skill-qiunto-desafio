import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from app import create_app

with TemporaryDirectory() as temp:
    dbpath = str(Path(temp) / "loja.db")
    app = create_app({"DATABASE": dbpath, "TESTING": True})
    c = app.test_client()
    checked = set()
    def check(method, url, status, data=None, route=None):
        r = c.open(url, method=method, json=data)
        assert r.status_code == status, (method, url, r.status_code, r.get_json())
        if route:
            checked.add((method, route))
            print(method, route, status)
        return r.get_json()
    check("GET", "/", 200, route="/")
    health = check("GET", "/health", 200, route="/health")
    assert "secret_key" not in health and health["database"] == "connected"
    products = check("GET", "/produtos", 200, route="/produtos")["dados"]
    stock = dict(nome="Kit d'arte", preco=10, estoque=3)
    pid = check("POST", "/produtos", 201, stock, "/produtos")["dados"]["id"]
    path = f"/produtos/{pid}"
    assert check("GET", "/produtos/busca?q=d%27arte", 200, route="/produtos/busca")["total"] == 1
    assert check("GET", path, 200, route="/produtos/<int:id>")["dados"]["estoque"] == 3
    check("PUT", path, 200, dict(stock, preco=20), "/produtos/<int:id>")
    u = dict(nome="Teste", email="teste@example.test", senha="Forte-2026!")
    uid = check("POST", "/usuarios", 201, u, "/usuarios")["dados"]["id"]
    assert all("senha" not in item for item in check("GET", "/usuarios", 200, route="/usuarios")["dados"])
    assert "senha" not in check("GET", f"/usuarios/{uid}", 200, route="/usuarios/<int:id>")["dados"]
    assert check("POST", "/login", 200, u, "/login")["dados"]["id"] == uid
    check("POST", "/login", 401, dict(u, senha="errada"))
    check("POST", "/usuarios", 409, dict(u, senha="outra-senha"))
    check("GET", "/produtos/busca?preco_min=abc", 400)
    check("POST", "/produtos", 400, dict(stock, estoque="3"))
    with closing(sqlite3.connect(dbpath)) as db:
        assert db.execute("SELECT senha FROM usuarios WHERE id = ?", (uid,)).fetchone()[0] != u["senha"]
        def inventory():
            return db.execute("SELECT estoque FROM produtos WHERE id = ?", (pid,)).fetchone()[0]
        item = dict(produto_id=pid, quantidade=2)
        check("POST", "/pedidos", 400, dict(usuario_id=uid, itens=[item, item]))
        assert inventory() == 3 and db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 0
        order = check("POST", "/pedidos", 201, dict(usuario_id=uid, itens=[item]), "/pedidos")["dados"]
        assert inventory() == 1 and order["total"] == 40
        for url, route in [("/pedidos", "/pedidos"), (f"/pedidos/usuario/{uid}", "/pedidos/usuario/<int:usuario_id>")]:
            orders = check("GET", url, 200, route=route)["dados"]
            assert orders[0]["itens"][0]["produto_nome"] == stock["nome"]
        oid = order["pedido_id"]
        check("PUT", f"/pedidos/{oid}/status", 200, {"status": "aprovado"}, "/pedidos/<int:pedido_id>/status")
        check("PUT", "/pedidos/99999/status", 404, {"status": "aprovado"})
        check("PUT", f"/pedidos/{oid}/status", 400, {"status": "inválido"})
        assert check("GET", "/relatorios/vendas", 200, route="/relatorios/vendas")["dados"]["faturamento_bruto"] == 40
        check("DELETE", path, 200, route="/produtos/<int:id>")
        assert db.execute("SELECT ativo FROM produtos WHERE id = ?", (pid,)).fetchone()[0] == 0
        assert check("GET", "/pedidos", 200)["dados"][0]["itens"][0]["produto_nome"] == stock["nome"]
        check("POST", "/admin/reset-db", 403, route="/admin/reset-db")
        check("POST", "/admin/query", 403, route="/admin/query")
        assert db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 1
    expected = {(method, rule.rule) for rule in app.url_map.iter_rules() if rule.endpoint != "static" for method in rule.methods - {"HEAD", "OPTIONS"}}
    assert len(checked) == 19 and checked == expected, expected - checked
    cli = app.test_cli_runner()
    r = cli.invoke(args=["reset-password", u["email"]], input="nova-senha\nnova-senha\n")
    assert r.exit_code == 0, r.output
    check("POST", "/login", 200, dict(u, senha="nova-senha"))
    r = cli.invoke(args=["reset-db"], input="y\n")
    assert r.exit_code == 0, r.output
    with closing(sqlite3.connect(dbpath)) as db:
        for table in ("produtos", "usuarios", "pedidos", "itens_pedido"):
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    print("PASS 19/19; estoque, hash, bloqueio HTTP e CLI local")
