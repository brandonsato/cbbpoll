from flask.ext.wtf import Form
from wtforms import TextField, SubmitField, FieldList, FormField, BooleanField
from flask.ext.admin.form.fields import Select2Field
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Email, Optional, DataRequired, Length, ValidationError
from cbbpoll import app
from models import Team

def allTeams():
    return Team.query

class LoginForm(Form):
    submit = SubmitField('Login/Sign Up via Reddit')


class EditProfileForm(Form):
    email = TextField('Email', validators = [Email(), Optional(), Length(max=120) ])
    emailReminders = BooleanField('Email Reminders')
    pmReminders = BooleanField('Reddit PM Reminders')
    submit = SubmitField('Save Changes')

class VoteForm(Form):
    team = QuerySelectField('Team', query_factory=allTeams, allow_blank=True, blank_text='Select a Team', 
        validators=[DataRequired(message="You must select a team.")])
    reason = TextField('Reason', validators=[Optional(), Length(max=140)])

class PollBallotForm(Form):
    votes = FieldList(FormField(VoteForm), min_entries=25, max_entries=25)
    submit = SubmitField('Submit Ballot')

    def validate_votes(form, field):
        seen = set()
        seen_twice = set()
        for vote in field:
            try:
                if vote.team.data.id in seen:
                    seen_twice.add(vote.team.data.id)
                else:
                    seen.add(vote.team.data.id)
            except AttributeError:
                # AttributeError ie, no team chosen. 
                # Allow DataRequired() validator to catch and display error.
                pass
        if seen_twice:
            teams = []
            for id in seen_twice:
                teams.append(str(Team.query.get(id))+ " appears more than once")
            raise ValidationError(", ".join(teams))
