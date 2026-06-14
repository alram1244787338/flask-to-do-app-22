"""Basic checks for the Flask to-do app.

Covers the things that were previously easy to break:
  * an empty database must render the home page (no manual table creation, no 500)
  * the task list must be ordered with the most recently touched task first
  * editing a task must float it back to the top
"""

import os
import tempfile
import time

# Point the app at a throwaway database *before* importing it, because
# Flask-SQLAlchemy binds its engine to the configured URI at import time.
_db_fd, _db_path = tempfile.mkstemp(suffix='.db')
os.environ['DATABASE_URL'] = 'sqlite:///' + _db_path

import pytest

from app import app, db
import models


@pytest.fixture(autouse=True)
def fresh_db():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield
    with app.app_context():
        db.session.remove()


@pytest.fixture
def client():
    return app.test_client()


def _create(client, title):
    return client.post('/add', data={'title': title}, follow_redirects=True)


def test_index_on_empty_db_returns_200_with_empty_state(client):
    """First run against an empty database renders instead of crashing."""
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'No tasks yet' in resp.data


def test_create_task_shows_created_feedback(client):
    resp = _create(client, 'Alpha')
    assert resp.status_code == 200
    assert b'Task created' in resp.data
    assert b'Alpha' in resp.data


def test_tasks_sorted_most_recent_first(client):
    _create(client, 'Alpha')
    time.sleep(0.01)
    _create(client, 'Bravo')

    body = client.get('/').get_data(as_text=True)
    # The task created last must appear before the earlier one.
    assert body.index('Bravo') < body.index('Alpha')


def test_edit_bumps_task_to_top(client):
    _create(client, 'Alpha')
    time.sleep(0.01)
    _create(client, 'Bravo')  # Bravo is now on top

    with app.app_context():
        alpha_id = models.Task.query.filter_by(title='Alpha').one().id

    time.sleep(0.01)
    resp = client.post(
        f'/edit/{alpha_id}', data={'title': 'Charlie'}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert b'Task updated' in resp.data

    body = client.get('/').get_data(as_text=True)
    # The just-edited task must now sit above the untouched one.
    assert body.index('Charlie') < body.index('Bravo')


def test_empty_title_is_not_saved(client):
    resp = client.post('/add', data={'title': ''}, follow_redirects=True)
    assert b'not saved' in resp.data
    with app.app_context():
        assert models.Task.query.count() == 0
