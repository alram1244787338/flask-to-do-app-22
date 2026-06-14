import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '8u3rouhfkjdsfiluh'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')

db = SQLAlchemy(app)

from routes import *  # noqa: E402,F401  (registers routes and the Task model)

# Make sure the schema exists on first run so an empty database does not 500.
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
