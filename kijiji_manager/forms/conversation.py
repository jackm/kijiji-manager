from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import InputRequired


class ConversationForm(FlaskForm):
    reply = TextAreaField('Reply', [InputRequired()])
