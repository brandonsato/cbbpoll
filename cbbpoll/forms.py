from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField
from wtforms.validators import Required, Length, Email, Optional
from cbbpoll import app

class LoginForm(Form):
    remember_me = BooleanField('remember_me', default = False)

class EditProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional()])

class AdminProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional()])
    role = SelectField('Role', choices=[(app.config['ROLE_USER'], 'User'),
        (app.config['ROLE_POLLSTER'], 'Pollster'),
        (app.config['ROLE_ADMIN'], 'Admin')], coerce=int)