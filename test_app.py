"""Tests for the Todo app fixes.

Covers the regression-prone areas called out by ops:
  * whitespace / blank titles must never reach the DB (add + edit)
  * editing or deleting a non-existent task_id returns a real 404
    (consistently for both GET and POST)
  * the happy-path add / edit / delete flows still work
"""

import pytest
from sqlalchemy.pool import StaticPool

from app import app, db
import models

# app.py binds the engine to sqlite:///site.db at import time, and
# Flask-SQLAlchemy creates engines eagerly in init_app (config changes after
# that are ignored). Re-point at an in-memory DB and rebuild the engine so the
# tests are fully isolated and never touch the real site.db.
app.config.update(
    TESTING=True,
    WTF_CSRF_ENABLED=False,
    SQLALCHEMY_DATABASE_URI="sqlite://",
    SQLALCHEMY_ENGINE_OPTIONS={
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    },
)
del app.extensions["sqlalchemy"]
db.init_app(app)


@pytest.fixture
def client():
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.session.remove()
        db.drop_all()


def _add(client, title, **kwargs):
    return client.post("/add", data={"title": title}, **kwargs)


def _count():
    with app.app_context():
        return models.Task.query.count()


def _first():
    with app.app_context():
        return models.Task.query.first()


# --- title hardening (req 1) ---------------------------------------------

def test_add_strips_surrounding_whitespace(client):
    resp = _add(client, "   Buy milk   ", follow_redirects=True)
    assert resp.status_code == 200
    task = _first()
    assert task is not None
    assert task.title == "Buy milk"


def test_add_blank_title_rejected(client):
    resp = _add(client, "   ")
    # form is re-rendered (200), not a redirect, and nothing is stored
    assert resp.status_code == 200
    assert _count() == 0
    assert b"Title is required and cannot be blank." in resp.data


def test_add_newline_only_title_rejected(client):
    resp = _add(client, "\n\n  \t")
    assert resp.status_code == 200
    assert _count() == 0
    assert b"Title is required and cannot be blank." in resp.data


def test_add_valid_title_creates_task(client):
    _add(client, "Real task", follow_redirects=True)
    assert _count() == 1


# --- editing an existing task to blank (req 2) ---------------------------

def test_edit_blank_title_rejected_keeps_original_and_shows_error(client):
    _add(client, "Original", follow_redirects=True)
    tid = _first().id

    resp = client.post(f"/edit/{tid}", data={"title": "   "})
    assert resp.status_code == 200
    assert b"Title is required and cannot be blank." in resp.data

    # the stored task must be untouched
    with app.app_context():
        assert db.session.get(models.Task, tid).title == "Original"


def test_edit_get_prefills_existing_title(client):
    _add(client, "Prefill me", follow_redirects=True)
    tid = _first().id
    resp = client.get(f"/edit/{tid}")
    assert resp.status_code == 200
    assert b"Prefill me" in resp.data


def test_edit_valid_update_strips_and_saves(client):
    _add(client, "old", follow_redirects=True)
    tid = _first().id
    resp = client.post(
        f"/edit/{tid}", data={"title": "  new title  "}, follow_redirects=True
    )
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(models.Task, tid).title == "new title"


# --- non-existent task_id (req 3, 4, 5) ----------------------------------

def test_edit_nonexistent_get_returns_404(client):
    resp = client.get("/edit/9999")
    assert resp.status_code == 404
    assert b"does not exist" in resp.data
    assert b"does not exit" not in resp.data  # the old typo is gone


def test_edit_nonexistent_post_returns_404(client):
    resp = client.post("/edit/9999", data={"title": "whatever"})
    assert resp.status_code == 404


def test_delete_nonexistent_get_returns_404(client):
    resp = client.get("/delete/9999")
    assert resp.status_code == 404
    assert b"does not exist" in resp.data
    assert b"does not exit" not in resp.data


def test_delete_nonexistent_post_returns_404(client):
    resp = client.post("/delete/9999", data={})
    assert resp.status_code == 404


def test_404_page_links_back_to_index(client):
    resp = client.get("/edit/9999")
    assert resp.status_code == 404
    assert b'href="/"' in resp.data or b"Back to Tasks" in resp.data


# --- delete GET/POST consistency + happy path (req 4, 6) -----------------

def test_delete_get_shows_confirmation_without_deleting(client):
    _add(client, "Keep me", follow_redirects=True)
    tid = _first().id
    resp = client.get(f"/delete/{tid}")
    assert resp.status_code == 200
    assert b"Keep me" in resp.data
    assert _count() == 1  # a GET must never delete


def test_delete_post_removes_task(client):
    _add(client, "Remove me", follow_redirects=True)
    tid = _first().id
    resp = client.post(f"/delete/{tid}", data={}, follow_redirects=True)
    assert resp.status_code == 200
    assert _count() == 0
