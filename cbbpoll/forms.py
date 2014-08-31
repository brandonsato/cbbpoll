from flask.ext.wtf import Form
from wtforms import TextField, SelectField, SubmitField, FieldList, FormField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required, Email, Optional, DataRequired, Length
from cbbpoll import app
from models import Team

def allTeams():
    return Team.query

class LoginForm(Form):
    submit = SubmitField('Login/Sign Up via Reddit');


class EditProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional(), Length(max=120) ])
    submit = SubmitField('Save Changes')

class AdminProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional(), Length(max=120)])
    role = SelectField('Role', choices=[(app.config['ROLE_USER'], 'User'),
        (app.config['ROLE_POLLSTER'], 'Pollster'),
        (app.config['ROLE_ADMIN'], 'Admin')], coerce=int)
    submit = SubmitField('Save Changes')


class VoteForm(Form):
    team = QuerySelectField('Team', query_factory=allTeams, allow_blank=True, blank_text='Select a Team', 
        validators=[DataRequired(message="You must select a team.")])
    reason = TextField('Reason', validators=[Optional(), Length(max=140)])

class PollBallotForm(Form):
    votes = FieldList(FormField(VoteForm), min_entries=25, max_entries=25)
    submit = SubmitField('Submit Ballot')
