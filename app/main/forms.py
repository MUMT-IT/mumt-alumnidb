from flask_wtf import FlaskForm
from wtforms.fields.simple import PasswordField, BooleanField
from wtforms.validators import DataRequired
from wtforms_components import StringField


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])