from utils.clock import utc_now
from flask import g, request, jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime
from services.statistics import scoped_tasks, task_statistics
from sqlalchemy.orm import joinedload


def get_tasks():
    tasks = scoped_tasks(g.actor).options(joinedload(Task.user), joinedload(Task.category)).all()
    return jsonify([
        dict(
            task.to_dict(),
            overdue=task.is_overdue(),
            user_name=task.user.name if task.user else None,
            category_name=task.category.name if task.category else None,
        )
        for task in tasks
    ]), 200

def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(dict(task.to_dict(), overdue=task.is_overdue())), 200

def create_task():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    title = data.get('title')
    if not isinstance(title, str) or not title:
        return jsonify({'error': 'Título é obrigatório'}), 400

    if len(title) < 3:
        return jsonify({'error': 'Título muito curto'}), 400

    if len(title) > 200:
        return jsonify({'error': 'Título muito longo'}), 400

    description = data.get('description', '')
    status = data.get('status', 'pending')
    priority = data.get('priority', 3)
    user_id = data.get('user_id')
    if not g.actor.is_admin():
        if 'user_id' in data and user_id != g.actor.id:
            return jsonify({'error': 'Acesso negado'}), 403
        user_id = g.actor.id
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    if status not in ['pending', 'in_progress', 'done', 'cancelled']:
        return jsonify({'error': 'Status inválido'}), 400

    if type(priority) is not int or not 1 <= priority <= 5:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

    if user_id:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    if category_id:
        cat = db.session.get(Category, category_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task()
    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except (TypeError, ValueError):
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    if tags:
        if type(tags) == list:
            task.tags = ','.join(tags)
        else:
            task.tags = tags

    db.session.add(task)
    db.session.commit()
    print(f"Task criada: {task.id} - {task.title}")
    return jsonify(task.to_dict()), 201

def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'title' in data:
        if not isinstance(data['title'], str) or len(data['title']) < 3:
            return jsonify({'error': 'Título muito curto'}), 400
        if len(data['title']) > 200:
            return jsonify({'error': 'Título muito longo'}), 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in ['pending', 'in_progress', 'done', 'cancelled']:
            return jsonify({'error': 'Status inválido'}), 400
        task.status = data['status']

    if 'priority' in data:
        if type(data['priority']) is not int or not 1 <= data['priority'] <= 5:
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
        task.priority = data['priority']

    if 'user_id' in data:
        if not g.actor.is_admin() and data['user_id'] != g.actor.id:
            return jsonify({'error': 'Acesso negado'}), 403
        if data['user_id']:
            user = db.session.get(User, data['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            cat = db.session.get(Category, data['category_id'])
            if not cat:
                return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except (TypeError, ValueError):
                return jsonify({'error': 'Formato de data inválido'}), 400
        else:
            task.due_date = None

    if 'tags' in data:
        if type(data['tags']) == list:
            task.tags = ','.join(data['tags'])
        else:
            task.tags = data['tags']

    task.updated_at = utc_now()

    db.session.commit()
    print(f"Task atualizada: {task.id}")
    return jsonify(task.to_dict()), 200

def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    db.session.delete(task)
    db.session.commit()
    print(f"Task deletada: {task_id}")
    return jsonify({'message': 'Task deletada com sucesso'}), 200

def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    tasks = scoped_tasks(g.actor)

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    for value, column, field in ((priority, Task.priority, 'priority'), (user_id, Task.user_id, 'user_id')):
        if value:
            try:
                number = int(value)
            except ValueError:
                return jsonify({'error': f'Filtro {field} inválido'}), 400
            if not 1 <= number <= (5 if field == 'priority' else 2**63 - 1):
                return jsonify({'error': f'Filtro {field} inválido'}), 400
            tasks = tasks.filter(column == number)

    results = tasks.all()
    output = []
    for t in results:
        output.append(t.to_dict())

    return jsonify(output), 200

def task_stats():
    return jsonify(task_statistics(scoped_tasks(g.actor))), 200
