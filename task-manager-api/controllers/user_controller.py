from utils.clock import utc_now
from flask import g, request, jsonify
from database import db
from models.user import User
from models.task import Task
from services.auth import issue_token
from sqlalchemy.orm import selectinload
import re


def get_users():
    users = User.query.options(selectinload(User.tasks)).all()
    result = []
    for u in users:
        user_data = {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'active': u.active,
            'created_at': str(u.created_at),
            'task_count': len(u.tasks)
        }
        result.append(user_data)
    return jsonify(result), 200

def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = user.to_dict()

    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = []
    for t in tasks:
        data['tasks'].append(t.to_dict())

    return jsonify(data), 200

def create_user():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'Nome é obrigatório'}), 400
    if not isinstance(email, str) or not email:
        return jsonify({'error': 'Email é obrigatório'}), 400
    if not isinstance(password, str) or not password:
        return jsonify({'error': 'Senha é obrigatória'}), 400

    if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
        return jsonify({'error': 'Email inválido'}), 400

    if len(password) < 4:
        return jsonify({'error': 'Senha deve ter no mínimo 4 caracteres'}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({'error': 'Email já cadastrado'}), 409

    if role != 'user':
        return jsonify({'error': 'Cadastro público permite apenas o papel user'}), 403

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    db.session.add(user)
    db.session.commit()
    print(f"Usuário criado: {user.id} - {user.name}")

    response_data = user.to_dict()
    return jsonify(response_data), 201

def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if not g.actor.is_admin() and {'role', 'active'}.intersection(data):
        return jsonify({'error': 'Acesso negado'}), 403

    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            return jsonify({'error': 'Nome inválido'}), 400
        user.name = data['name']

    if 'email' in data:
        if not isinstance(data['email'], str) or not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', data['email']):
            return jsonify({'error': 'Email inválido'}), 400

        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email já cadastrado'}), 409
        user.email = data['email']

    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < 4:
            return jsonify({'error': 'Senha muito curta'}), 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in ['user', 'admin', 'manager']:
            return jsonify({'error': 'Role inválido'}), 400
        user.role = data['role']

    if 'active' in data:
        if type(data['active']) is not bool:
            return jsonify({'error': 'Active inválido'}), 400
        user.active = data['active']

    db.session.commit()
    return jsonify(user.to_dict()), 200

def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    db.session.delete(user)
    db.session.commit()
    print(f"Usuário deletado: {user_id}")
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200

def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for t in tasks:
        task_data = {}
        task_data['id'] = t.id
        task_data['title'] = t.title
        task_data['description'] = t.description
        task_data['status'] = t.status
        task_data['priority'] = t.priority
        task_data['created_at'] = str(t.created_at)
        task_data['due_date'] = str(t.due_date) if t.due_date else None

        if t.due_date:
            if t.due_date < utc_now():
                if t.status != 'done' and t.status != 'cancelled':
                    task_data['overdue'] = True
                else:
                    task_data['overdue'] = False
            else:
                task_data['overdue'] = False
        else:
            task_data['overdue'] = False
        result.append(task_data)

    return jsonify(result), 200

def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')

    if not all(isinstance(value, str) and value for value in (email, password)):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401

    if not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    if not user.active:
        return jsonify({'error': 'Usuário inativo'}), 403

    if user.uses_legacy_password():
        user.set_password(password)
        db.session.commit()

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user)
    }), 200
