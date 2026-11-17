from flask import Blueprint, jsonify
import controllers
from settings import API_VERSION

routes = Blueprint("store", __name__)

routes.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
routes.add_url_rule("/produtos/busca", "buscar_produtos", controllers.buscar_produtos, methods=["GET"])
routes.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
routes.add_url_rule("/produtos", "criar_produto", controllers.criar_produto, methods=["POST"])
routes.add_url_rule("/produtos/<int:id>", "atualizar_produto", controllers.atualizar_produto, methods=["PUT"])
routes.add_url_rule("/produtos/<int:id>", "deletar_produto", controllers.deletar_produto, methods=["DELETE"])

routes.add_url_rule("/usuarios", "listar_usuarios", controllers.listar_usuarios, methods=["GET"])
routes.add_url_rule("/usuarios/<int:id>", "buscar_usuario", controllers.buscar_usuario, methods=["GET"])
routes.add_url_rule("/usuarios", "criar_usuario", controllers.criar_usuario, methods=["POST"])
routes.add_url_rule("/login", "login", controllers.login, methods=["POST"])

routes.add_url_rule("/pedidos", "criar_pedido", controllers.criar_pedido, methods=["POST"])
routes.add_url_rule("/pedidos", "listar_todos_pedidos", controllers.listar_todos_pedidos, methods=["GET"])
routes.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", controllers.listar_pedidos_usuario, methods=["GET"])
routes.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controllers.atualizar_status_pedido, methods=["PUT"])

routes.add_url_rule("/relatorios/vendas", "relatorio_vendas", controllers.relatorio_vendas, methods=["GET"])

routes.add_url_rule("/health", "health_check", controllers.health_check, methods=["GET"])

@routes.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": API_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })


@routes.post("/admin/reset-db")
@routes.post("/admin/query")
def blocked_admin_operation():
    return jsonify({"erro": "Operação administrativa indisponível por HTTP"}), 403
