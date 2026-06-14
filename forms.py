from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, StopValidation


def cleaned_title(form, field):
    """Strip leading/trailing whitespace and reject blank titles."""
    original = field.data
    field.data = field.data.strip() if field.data else ''
    if not field.data:
        raise StopValidation('Title cannot be empty or blank.')


class AddTaskForm(FlaskForm):
    title = StringField('Title', validators=[cleaned_title, DataRequired()])
    submit = SubmitField('Submit')


class DeleteTaskForm(FlaskForm):
    submit = SubmitField('Delete')
