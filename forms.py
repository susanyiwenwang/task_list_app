from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, validators, PasswordField
from wtforms.validators import DataRequired, URL


# format='%m/%d/%Y'
class TaskEntry(FlaskForm):
    entry = StringField("Next on the to-do list:", validators=[DataRequired()])
    due_date = DateField("Due date (optional):", validators=[validators.Optional()])
    submit = SubmitField("Add new task")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
