from datetime import timedelta

from sqlalchemy import case, func

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import utc_now

STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
PRIORITIES = ('critical', 'high', 'medium', 'low', 'minimal')


def scoped_tasks(actor):
    return Task.query if actor.is_admin() else Task.query.filter_by(user_id=actor.id)


def overdue_at(now):
    return (Task.due_date < now) & (Task.status.is_(None) | Task.status.notin_(('done', 'cancelled')))


def count_if(condition):
    return func.count(case((condition, 1)))


def task_statistics(tasks, now=None):
    now = now or utc_now()
    total, *counts = tasks.with_entities(
        func.count(Task.id),
        *(count_if(Task.status == status) for status in STATUSES),
        count_if(overdue_at(now)),
    ).one()
    stats = dict(zip((*STATUSES, 'overdue'), counts))
    return dict(stats, total=total, completion_rate=percentage(stats['done'], total))


def percentage(done, total):
    return round((done / total) * 100, 2) if total else 0


def user_statistics(user):
    tasks = Task.query.filter_by(user_id=user.id)
    stats = task_statistics(tasks)
    stats['total_tasks'] = stats.pop('total')
    stats['high_priority'] = tasks.filter(Task.priority <= 2).count()
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': stats,
    }


def summary_statistics():
    now = utc_now()
    tasks = Task.query
    stats = task_statistics(tasks, now)
    counts = dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())
    overdue = tasks.filter(overdue_at(now)).order_by(Task.id).with_entities(
        Task.id, Task.title, Task.due_date
    ).all()
    since = now - timedelta(days=7)
    productivity = db.session.query(
        User.id, User.name, func.count(Task.id), count_if(Task.status == 'done')
    ).outerjoin(Task, Task.user_id == User.id).group_by(User.id, User.name).order_by(User.id).all()
    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': stats['total'],
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': {status: stats[status] for status in STATUSES},
        'tasks_by_priority': {label: counts.get(index, 0) for index, label in enumerate(PRIORITIES, 1)},
        'overdue': {
            'count': stats['overdue'],
            'tasks': [
                {'id': id, 'title': title, 'due_date': str(due), 'days_overdue': (now - due).days}
                for id, title, due in overdue
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': tasks.filter(Task.created_at >= since).count(),
            'tasks_completed_last_7_days': tasks.filter(Task.status == 'done', Task.updated_at >= since).count(),
        },
        'user_productivity': [
            {'user_id': id, 'user_name': name, 'total_tasks': total,
             'completed_tasks': done, 'completion_rate': percentage(done, total)}
            for id, name, total, done in productivity
        ],
    }


def category_counts(actor):
    counts = scoped_tasks(actor).with_entities(
        Task.category_id.label('category_id'), func.count(Task.id).label('count')
    ).group_by(Task.category_id).subquery()
    rows = db.session.query(Category, counts.c.count).outerjoin(
        counts, counts.c.category_id == Category.id
    ).order_by(Category.id).all()
    return [dict(category.to_dict(), task_count=count or 0) for category, count in rows]
