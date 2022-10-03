from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import InputRequired


class ConversationForm(FlaskForm):
    """User conversation form."""
    message = TextAreaField('Reply', [InputRequired()])
    submit = SubmitField('Reply')
