from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, FieldList, FormField, BooleanField, TextAreaField, widgets
from wtforms_alchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import Email, Optional, DataRequired, Length, ValidationError
from cbbpoll import app
from models import Team, ConsumptionTag

def all_teams():
    return Team.query

class LoginForm(Form):
    submit = SubmitField('Login/Sign Up via Reddit')

class ListCheckboxWidget(widgets.ListWidget):
  def __call__(self, field, **kwargs):
    kwargs.setdefault('id', field.id)

    html = ["\n"]

    for subfield in field:
      html.append(u'<div class="checkbox"><label>%s%s</label></div>\n' % (subfield(), subfield.label.text))

    return widgets.HTMLString(u''.join(html))

class QueryMultiCheckboxField(QuerySelectMultipleField):
  widget = ListCheckboxWidget()
  option_widget = widgets.CheckboxInput()

  def iter_choices(self):
    for pk, obj in self._get_object_list():
      if hasattr(obj, self.id):
        selected = getattr(obj, self.id)
      else:
        selected = obj in self.data

      yield (pk, self.get_label(obj), selected)

class EditProfileForm(Form):
    email = StringField('Email', validators = [Email(), Optional(), Length(max=120) ])
    emailReminders = BooleanField('Email Reminders')
    pmReminders = BooleanField('Reddit PM Reminders')
    submit = SubmitField('Save Changes')

class VoteForm(Form):
    team = QuerySelectField('Team', query_factory=all_teams, allow_blank=True, blank_text='Select a Team',
        validators=[DataRequired(message="You must select a team.")])
    reason = StringField('Reason', validators=[Optional(), Length(max=140)])

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

class VoterApplicationForm(Form):
    primary_team_id = QuerySelectField('Which team do you Primarily support?',
        query_factory=all_teams, allow_blank=True, blank_text='Select a Team',
        validators=[DataRequired(message="You must select a team.")])
    other_teams = QuerySelectMultipleField('Which other teams, if any, do you support?',
        query_factory=all_teams)
    consumption_tags = QueryMultiCheckboxField('In which of the following ways do you inform your opinion of basketball teams? (select all that apply)', query_factory=lambda: ConsumptionTag.query.all(), option_widget=widgets.CheckboxInput())
    approach = TextAreaField('If selected, how would you approach filling out your ballot? What would lead you to decide to vote for one team over another?', [DataRequired(), Length(max=1000)])
    other_comments = TextAreaField('Anything else to say?', [Optional(), Length(max=1000)])
    will_participate = BooleanField('''I understand that there is a participation requirement to this poll. \
        If I fail to submit a ballot three times, I understand that I may lose voting privilege''',
         validators=[DataRequired()])
    season=2016
    submit = SubmitField('Submit Application')
