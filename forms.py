from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


def strip_whitespace(value):
    """Trim surrounding whitespace so titles never enter the DB dirty.

    Runs as a WTForms input filter (before validators), so a title made up
    only of spaces/newlines collapses to '' and is then rejected by
    DataRequired.
    """
    if isinstance(value, str):
        return value.strip()
    return value


class AddTaskForm(FlaskForm):
    title = StringField(
        'Title',
        filters=[strip_whitespace],
        validators=[DataRequired(message='Title is required and cannot be blank.')],
    )
    submit = SubmitField('Submit')


class DeleteTaskForm(FlaskForm):
    submit = SubmitField('Delete')
