from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required, Length, Email

class LoginForm(Form):
    remember_me = BooleanField('remember_me', default = False)

class EditProfileForm(Form):
    email = TextField('email', validators = [Email()])