from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '8u3rouhfkjdsfiluh'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


from routes import *

if __name__ == '__main__':
    app.run(debug=True)
