import os
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from database import db
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.auth import authorize
from settings import load_config


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if config:
        app.config.update(config)
    CORS(app)
    db.init_app(app)

    for blueprint in (task_bp, user_bp, report_bp):
        app.register_blueprint(blueprint)
    app.before_request(authorize)

    @app.get('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    @app.get('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def internal_error(error):
        db.session.rollback()
        app.logger.error('Falha interna do Task Manager', exc_info=error)
        return jsonify({'error': 'Erro interno'}), 500

    with app.app_context():
        db.create_all()
    return app


if __name__ == '__main__':
    create_app().run(
        host=os.getenv('TASK_HOST', '127.0.0.1'),
        port=int(os.getenv('TASK_PORT', '5000')),
        debug=False,
    )
