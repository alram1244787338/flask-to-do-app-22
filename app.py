import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '8u3rouhfkjdsfiluh'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

from routes import *


def _migrate_database():
    """Auto-migrate existing database to the new schema."""
    candidates = [
        os.path.join(app.instance_path, 'site.db'),
        os.path.join(os.getcwd(), 'site.db'),
    ]
    db_path = None
    for p in candidates:
        if os.path.exists(p):
            db_path = p
            break
    if db_path is None:
        return
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(task)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if 'date' in existing_columns:
        if 'created_at' not in existing_columns:
            cursor.execute("ALTER TABLE task ADD COLUMN created_at DATETIME")
            cursor.execute("UPDATE task SET created_at = date")
            cursor.execute("ALTER TABLE task ADD COLUMN updated_at DATETIME")
            conn.commit()
        # Drop old date column (requires SQLite >= 3.35.0)
        try:
            cursor.execute("ALTER TABLE task DROP COLUMN date")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    conn.close()


with app.app_context():
    _migrate_database()
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
