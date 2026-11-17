import os

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from database import close_db, get_db, init_db
from routes import routes
from settings import load_config


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if config:
        app.config.update(config)
    CORS(app)
    app.register_blueprint(routes)
    app.cli.add_command(reset_db)
    app.cli.add_command(reset_password)
    app.teardown_appcontext(close_db)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify({"erro": error.description}), error.code

    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.error("Erro interno em operação da loja", exc_info=error)
        return jsonify({"erro": "Erro interno"}), 500

    with app.app_context():
        init_db()
    return app


@click.command("reset-db")
@click.confirmation_option(prompt="Excluir todos os dados da loja?")
@with_appcontext
def reset_db():
    """Reset the store database using local operating-system access."""
    db = get_db()
    with db:
        db.execute("DELETE FROM itens_pedido")
        db.execute("DELETE FROM pedidos")
        db.execute("DELETE FROM produtos")
        db.execute("DELETE FROM usuarios")
    click.echo("Banco de dados resetado")


@click.command("reset-password")
@click.argument("email")
@click.option("--user-id", type=click.IntRange(min=1), help="ID da conta quando o e-mail estiver duplicado.")
@with_appcontext
def reset_password(email, user_id):
    """Set a new password for an existing account."""
    senha = click.prompt("Nova senha", hide_input=True, confirmation_prompt=True)
    if not senha:
        raise click.ClickException("Senha obrigatória")
    db = get_db()
    with db:
        sql = "UPDATE usuarios SET senha = ? WHERE email = ?"
        params = (generate_password_hash(senha), email)
        if user_id is not None:
            sql += " AND id = ?"
            params += (user_id,)
        result = db.execute(sql, params)
        if result.rowcount != 1:
            raise click.ClickException("Informe um e-mail único ou especifique o ID da conta com --user-id")
    click.echo("Senha redefinida")


if __name__ == "__main__":
    create_app().run(host=os.getenv("LOJA_HOST", "127.0.0.1"), port=int(os.getenv("LOJA_PORT", "5000")), debug=False)
