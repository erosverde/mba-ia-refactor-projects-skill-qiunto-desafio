import hashlib
import hmac

from flask import abort, current_app, g, request
from itsdangerous import BadData, URLSafeTimedSerializer

from database import db
from models.task import Task
from models.user import User

PUBLIC_ENDPOINTS = {'index', 'health', 'users.login', 'users.create_user'}
ADMIN_ENDPOINTS = {
    'users.get_users', 'users.delete_user', 'reports.summary_report',
    'reports.create_category', 'reports.update_category', 'reports.delete_category',
}


def serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt='task-manager-access')


def credential_version(user):
    return hmac.new(current_app.secret_key.encode(), user.password.encode(), hashlib.sha256).hexdigest()


def issue_token(user):
    return serializer().dumps({'sub': user.id, 'ver': credential_version(user)})


def authorize():
    endpoint = request.endpoint
    if endpoint is None or endpoint in PUBLIC_ENDPOINTS or request.method == 'OPTIONS':
        return

    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme.lower() != 'bearer' or not token:
        abort(401)
    try:
        payload = serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE'])
    except BadData:
        abort(401)

    user = db.session.get(User, payload['sub'])
    if user is None or not user.active or not hmac.compare_digest(payload['ver'], credential_version(user)):
        abort(401)
    g.actor = user
    if user.is_admin():
        return

    if endpoint in ADMIN_ENDPOINTS:
        abort(403)
    args = request.view_args or {}
    if 'user_id' in args and args['user_id'] != user.id:
        abort(403)
    if 'task_id' in args:
        task = db.session.get(Task, args['task_id'])
        if task is None:
            abort(404, description='Task não encontrada')
        if task.user_id != user.id:
            abort(403)
