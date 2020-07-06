from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import InputRequired


class ConversationForm(FlaskForm):
    message = TextAreaField('Reply', [InputRequired()])
    submit = SubmitField('Reply')
