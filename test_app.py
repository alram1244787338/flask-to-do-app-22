import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
import models


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


# ---------- Add: blank title ----------

def test_add_empty_title(client):
    resp = client.post('/add', data={'title': ''})
    assert resp.status_code == 200
    assert b'Title cannot be empty or blank' in resp.data


def test_add_whitespace_title(client):
    resp = client.post('/add', data={'title': '   \n\t  '})
    assert resp.status_code == 200
    assert b'Title cannot be empty or blank' in resp.data


def test_add_newlines_only_title(client):
    resp = client.post('/add', data={'title': '\n\n\n'})
    assert resp.status_code == 200
    assert b'Title cannot be empty or blank' in resp.data


# ---------- Add: whitespace stripping ----------

def test_add_strips_whitespace(client):
    resp = client.post('/add', data={'title': '  Hello World  '}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Task added' in resp.data
    with app.app_context():
        task = models.Task.query.first()
        assert task is not None
        assert task.title == 'Hello World'


# ---------- Edit: non-existent task ----------

def test_edit_nonexistent_get(client):
    resp = client.get('/edit/9999')
    assert resp.status_code == 404


def test_edit_nonexistent_post(client):
    resp = client.post('/edit/9999', data={'title': 'whatever'})
    assert resp.status_code == 404


# ---------- Edit: blank title ----------

def test_edit_blank_title(client):
    with app.app_context():
        task = models.Task(title='Original Title', date=datetime.utcnow())
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    resp = client.post(f'/edit/{task_id}', data={'title': '   '})
    assert resp.status_code == 200
    assert b'Title cannot be empty or blank' in resp.data

    # Verify original title is preserved in DB
    with app.app_context():
        task = db.session.get(models.Task, task_id)
        assert task.title == 'Original Title'


def test_edit_strips_whitespace(client):
    with app.app_context():
        task = models.Task(title='Original', date=datetime.utcnow())
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    resp = client.post(f'/edit/{task_id}', data={'title': '  Updated Title  '}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Task updated' in resp.data

    with app.app_context():
        task = db.session.get(models.Task, task_id)
        assert task.title == 'Updated Title'


# ---------- Delete: non-existent task ----------

def test_delete_nonexistent_get(client):
    resp = client.get('/delete/9999')
    assert resp.status_code == 404


def test_delete_nonexistent_post(client):
    resp = client.post('/delete/9999')
    assert resp.status_code == 404


# ---------- Normal flow smoke tests ----------

def test_add_and_delete_flow(client):
    # Add
    resp = client.post('/add', data={'title': 'My Task'}, follow_redirects=True)
    assert b'Task added' in resp.data

    with app.app_context():
        task = models.Task.query.first()
        task_id = task.id

    # Delete GET shows confirmation
    resp = client.get(f'/delete/{task_id}')
    assert resp.status_code == 200
    assert b'My Task' in resp.data

    # Delete POST removes the task
    resp = client.post(f'/delete/{task_id}', follow_redirects=True)
    assert b'Task deleted' in resp.data

    with app.app_context():
        assert db.session.get(models.Task, task_id) is None
