from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired


class LoginForm(FlaskForm):
    email_icon = Markup('<i class="fas fa-user"></i>')
    email = StringField(email_icon, [InputRequired()], render_kw={'placeholder': 'Email'})
    password_icon = Markup('<i class="fas fa-lock"></i>')
    password = PasswordField(password_icon, [InputRequired()], render_kw={'placeholder': 'Password'})
