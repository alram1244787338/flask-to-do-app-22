import os
import tempfile
import unittest
from datetime import datetime

from app import app, db
import models


class TaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + self.db_path
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _add_task(self, title='Example'):
        task = models.Task(title=title)
        db.session.add(task)
        db.session.commit()
        task_id = task.id
        db.session.remove()
        return task_id

    def _get(self, task_id):
        db.session.expire_all()
        return db.session.get(models.Task, task_id)

    # --- Delete must go through an explicit POST submission ---

    def test_get_delete_renders_confirmation_without_deleting(self):
        task_id = self._add_task()
        resp = self.client.get(f'/delete/{task_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Are you sure', resp.data)
        # The task must still exist: a GET never mutates data.
        self.assertIsNotNone(self._get(task_id))

    def test_post_delete_removes_task(self):
        task_id = self._add_task()
        resp = self.client.post(f'/delete/{task_id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Task deleted', resp.data)
        self.assertIsNone(self._get(task_id))

    # --- Editing bumps updated_at but never created_at ---

    def test_edit_updates_updated_at_only(self):
        task_id = self._add_task(title='Original')
        past = datetime(2020, 1, 1, 12, 0, 0)
        task = self._get(task_id)
        task.created_at = past
        task.updated_at = past
        db.session.commit()
        db.session.remove()

        resp = self.client.post(
            f'/edit/{task_id}', data={'title': 'Changed'}, follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Task updated', resp.data)

        task = self._get(task_id)
        self.assertEqual(task.title, 'Changed')
        self.assertEqual(task.created_at, past)  # creation time is preserved
        self.assertGreater(task.updated_at, past)  # update time moved forward

    # --- Homepage no longer misleads about time and has no plain delete link ---

    def test_index_distinguishes_created_and_updated(self):
        self._add_task()
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Created on', resp.data)
        self.assertIn(b'Last updated', resp.data)
        # The old misleading label is gone.
        self.assertNotIn(b'Added on', resp.data)

    def test_index_delete_is_a_button_not_a_plain_link(self):
        self._add_task()
        resp = self.client.get('/')
        # Delete is rendered as a form button, not a crawlable hyperlink.
        self.assertIn(b'<button type="submit" class="btn btn-danger">Delete</button>', resp.data)
        self.assertNotIn(b'href="/delete/', resp.data)


if __name__ == '__main__':
    unittest.main()
