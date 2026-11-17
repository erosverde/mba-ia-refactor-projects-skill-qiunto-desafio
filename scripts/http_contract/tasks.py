import hashlib
from datetime import datetime, timedelta

def populate(app, db, User, Task, Category):
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    with app.app_context():
        ids = []
        for name, role in [('Admin', 'admin'), ('Alice', 'user'), ('Bob', 'user')]:
            user = User(name=name, email=name.lower()+'@example.test', role=role)
            user.password = hashlib.md5(b'fixture-password').hexdigest()
            db.session.add(user)
            db.session.flush()
            ids.append(user.id)
        category = Category(name='Infra')
        db.session.add(category)
        db.session.flush()
        cid = category.id
        for index, status in enumerate(['pending', 'done', 'in_progress', 'cancelled'], 1):
            db.session.add(Task(title=f'Tarefa {index}', status=status, priority=index,
                user_id=ids[1 if index < 3 else 2], category_id=cid,
                due_date=now - timedelta(days=3), created_at=now, updated_at=now))
        db.session.commit()
        return ids

from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import ExitStack
from app import create_app
from database import db
from models.user import User
from models.task import Task
from models.category import Category
from sqlalchemy import event

EXPECTED_STATS = {
    'total': 4, 'pending': 1, 'in_progress': 1, 'done': 1,
    'cancelled': 1, 'overdue': 2, 'completion_rate': 25.0,
}

with ExitStack() as cleanup:
    d = cleanup.enter_context(TemporaryDirectory())
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///'+Path(d,'test.db').as_posix(), 'TESTING': True})
    with app.app_context():
        cleanup.callback(db.engine.dispose)
    admin_id, alice_id, bob_id = populate(app, db, User, Task, Category)
    client = app.test_client()
    seen = set()
    def call(method,url,status, data=None, token=None, route=None):
        headers = {'Authorization':'Bearer '+token} if token else {}
        r = client.open(url, method=method,json=data,headers=headers)
        assert r.status_code == status,(method,url,r.status_code,r.get_json())
        if route:
            seen.add((method,route))
            print(method,route,r.status_code)
        return r.get_json()
    call('GET','/',200,route='/')
    call('GET','/health',200,route='/health')
    def login(name, route=None):
        result = call('POST','/login',200,{'email':name+'@example.test','password':'fixture-password'},route=route)
        assert 'password' not in result['user']
        return result['token']
    admin = login('admin','/login')
    alice = login('alice')
    bob = login('bob')
    with app.app_context():
        assert all(user.password.startswith('scrypt:') for user in User.query.all())
    call('GET','/tasks',401)
    call('GET','/tasks',401,token=alice+'tamper')
    call('GET','/users',403,token=alice)
    call('GET',f'/users/{bob_id}',403,token=alice)
    call('PUT',f'/users/{alice_id}',403,{'role':'admin'},alice)
    call('GET','/reports/summary',403,token=alice)
    call('GET',f'/reports/user/{bob_id}',403,token=alice)
    call('GET','/tasks/3',403,token=alice)
    call('PUT','/tasks/3',403,{'title':'Bloqueada'},alice)
    call('DELETE','/tasks/3',403,token=alice)
    call('POST','/tasks',403,{'title':'Negada','user_id':bob_id},alice)
    call('POST','/categories',403,{'name':'Bloqueada'},alice)
    call('POST','/users',403,{'name':'Elevado','email':'e@example.test','password':'senha segura','role':'admin'})
    call('GET','/tasks/search?priority=abc',400,token=alice)
    call('GET','/tasks/search?user_id=abc',400,token=alice)
    call('POST','/login',401,{'email':'alice@example.test','password':'errada'})
    with app.app_context():
        engine = db.engine
    sql_reads = []
    def count_read(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('SELECT'):
            sql_reads.append(statement)
    event.listen(engine,'before_cursor_execute',count_read)
    try:
        assert len(call('GET','/tasks',200,token=admin,route='/tasks')) == 4
        print('GET /tasks SELECTs incluindo autenticação:',len(sql_reads))
        assert len(sql_reads) == 2
    finally:
        event.remove(engine,'before_cursor_execute',count_read)
    tasks = call('GET','/tasks',200,token=alice)
    assert len(tasks) == 2 and all(row['user_id'] == alice_id for row in tasks)
    assert len(call('GET','/tasks/search',200,token=alice,route='/tasks/search')) == 2
    assert call('GET',f'/tasks/search?user_id={bob_id}',200,token=alice) == []
    assert call('GET','/tasks/1',200,token=alice,route='/tasks/<int:task_id>')['overdue']
    assert call('GET', '/tasks/stats', 200, token=admin, route='/tasks/stats') == EXPECTED_STATS
    summary = call('GET', '/reports/summary', 200, token=admin, route='/reports/summary')
    assert summary['overview'] == {'total_tasks': 4, 'total_users': 3, 'total_categories': 1}
    assert summary['tasks_by_status'] == {status: 1 for status in ('pending', 'in_progress', 'done', 'cancelled')}
    assert summary['tasks_by_priority'] == {'critical': 1, 'high': 1, 'medium': 1, 'low': 1, 'minimal': 0}
    assert summary['overdue']['count'] == 2
    assert [item['id'] for item in summary['overdue']['tasks']] == [1, 3]
    assert summary['recent_activity'] == {'tasks_created_last_7_days': 4, 'tasks_completed_last_7_days': 1}
    assert [item['completed_tasks'] for item in summary['user_productivity']] == [0, 1, 0]
    individual = call('GET', f'/reports/user/{alice_id}', 200, token=admin, route='/reports/user/<int:user_id>')
    assert individual['user']['id'] == alice_id
    assert individual['statistics'] == {
        'total_tasks': 2, 'done': 1, 'pending': 1, 'in_progress': 0, 'cancelled': 0,
        'overdue': 1, 'high_priority': 2, 'completion_rate': 50.0,
    }
    categories = call('GET', '/categories', 200, token=admin, route='/categories')
    assert [(item['name'], item['task_count']) for item in categories] == [('Infra', 4)]
    assert call('GET','/tasks/stats',200,token=alice)['total'] == 2
    assert call('GET','/categories',200,token=alice)[0]['task_count'] == 2
    assert 'password' not in call('GET',f'/users/{alice_id}',200,token=alice,route='/users/<int:user_id>')
    assert len(call('GET',f'/users/{alice_id}/tasks',200,token=alice,route='/users/<int:user_id>/tasks')) == 2
    assert len(call('GET','/users',200,token=admin,route='/users')) == 3
    new = call('POST','/users',201,{'name':'Carol','email':'carol@example.test','password':'local-senha'},route='/users')
    assert 'password' not in new and new['role'] == 'user'
    assert 'password' not in call('PUT',f'/users/{alice_id}',200,{'name':'Alice Silva'},alice,'/users/<int:user_id>')
    cat = call('POST','/categories',201,{'name':'Nova'},admin,'/categories')['id']
    call('PUT',f'/categories/{cat}',200,{'name':'Nova 2'},admin,'/categories/<int:cat_id>')
    task = call('POST','/tasks',201,{'title':'Minha tarefa','category_id':cat},alice,'/tasks')
    assert task['user_id'] == alice_id
    call('PUT',f"/tasks/{task['id']}",403,{'user_id':bob_id},alice)
    call('PUT',f"/tasks/{task['id']}",200,{'status':'done'},alice,'/tasks/<int:task_id>')
    call('DELETE',f"/tasks/{task['id']}",200,token=alice,route='/tasks/<int:task_id>')
    call('DELETE',f'/categories/{cat}',200,token=admin,route='/categories/<int:cat_id>')
    call('DELETE',f"/users/{new['id']}",200,token=admin,route='/users/<int:user_id>')
    call('PUT',f'/users/{alice_id}',200,{'password':'nova-senha'},alice)
    call('GET','/tasks',401,token=alice)
    call('POST','/login',200,{'email':'alice@example.test','password':'nova-senha'})
    declared = {(method, rule.rule) for rule in app.url_map.iter_rules()
                if rule.endpoint != 'static' for method in rule.methods - {'HEAD', 'OPTIONS'}}
    assert seen == declared, declared - seen
    assert len(seen) == 22
    app.config['TOKEN_MAX_AGE'] = -1
    call('GET','/tasks',401,token=bob)
    print('PASS 22/22; indicadores, autorização e migração de hash')
