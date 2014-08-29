from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, SubmitField
from wtforms.validators import Required, Length, Email, Optional
from cbbpoll import app

class LoginForm(Form):
    submit = SubmitField('Login/Sign Up via Reddit');

class EditProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional()])

class AdminProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional()])
    role = SelectField('Role', choices=[(app.config['ROLE_USER'], 'User'),
        (app.config['ROLE_POLLSTER'], 'Pollster'),
        (app.config['ROLE_ADMIN'], 'Admin')], coerce=int)