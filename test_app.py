import pytest
import os
import tempfile
from datetime import datetime
import time

from app import app, db
import models


@pytest.fixture
def client():
    """Create a test client with a fresh in-memory database."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_empty_db_starts_without_error(client):
    """Empty database should load the index page without a 500 error."""
    response = client.get('/')
    assert response.status_code == 200


def test_empty_state_message_shown(client):
    """Index page should show a helpful message when there are no tasks."""
    response = client.get('/')
    assert b'No tasks yet' in response.data


def test_create_task_shows_in_list(client):
    """After creating a task, it should appear on the index page."""
    client.post('/add', data={'title': 'Test task'})
    response = client.get('/')
    assert b'Test task' in response.data


def test_create_task_flash_message(client):
    """Creating a task should show a success flash message."""
    response = client.post('/add', data={'title': 'New task'}, follow_redirects=True)
    assert b'Task created successfully' in response.data


def test_newer_task_appears_first(client):
    """Tasks should be sorted by most recently updated first."""
    client.post('/add', data={'title': 'First task'})
    time.sleep(1)
    client.post('/add', data={'title': 'Second task'})

    response = client.get('/')
    html = response.data.decode()

    first_pos = html.index('First task')
    second_pos = html.index('Second task')

    # Second task (newer) should appear before First task (older)
    assert second_pos < first_pos


def test_edited_task_moves_to_top(client):
    """Editing a task should update its updated_at and move it to the top."""
    client.post('/add', data={'title': 'Task A'})
    time.sleep(1)
    client.post('/add', data={'title': 'Task B'})

    # At this point Task B is on top. Now edit Task A.
    time.sleep(1)
    client.post('/edit/1', data={'title': 'Task A edited'})

    response = client.get('/')
    html = response.data.decode()

    pos_a = html.index('Task A edited')
    pos_b = html.index('Task B')

    # Task A (just edited) should appear before Task B
    assert pos_a < pos_b


def test_edit_task_flash_message(client):
    """Editing a task should show an updated flash message."""
    client.post('/add', data={'title': 'Original'})
    response = client.post('/edit/1', data={'title': 'Updated'}, follow_redirects=True)
    assert b'Task updated successfully' in response.data


def test_delete_task_flash_message(client):
    """Deleting a task should show a deletion flash message."""
    client.post('/add', data={'title': 'To delete'})
    response = client.post('/delete/1', data={'submit': True}, follow_redirects=True)
    assert b'Task deleted successfully' in response.data


def test_edit_nonexistent_task(client):
    """Editing a task that doesn't exist should show an error message."""
    response = client.get('/edit/999', follow_redirects=True)
    assert b'does not exist' in response.data


def test_no_tasks_after_all_deleted(client):
    """After deleting all tasks, the empty state message should reappear."""
    client.post('/add', data={'title': 'Only task'})
    client.post('/delete/1', data={'submit': True})
    response = client.get('/')
    assert b'No tasks yet' in response.data
