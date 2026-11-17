from flask import g, request, jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from services.statistics import category_counts, summary_statistics, user_statistics


def summary_report():
    return jsonify(summary_statistics()), 200

def user_report(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user_statistics(user)), 200

def get_categories():
    return jsonify(category_counts(g.actor)), 200

def create_category():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')

    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201

def update_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    db.session.commit()
    return jsonify(cat.to_dict()), 200

def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message': 'Categoria deletada'}), 200
