from flask import redirect, url_for
from flask.ext import admin
from flask.ext.admin import expose
from flask.ext.admin.contrib import sqla
from flask.ext.admin.form.fields import Select2Field
from flask.ext.admin.form import FormOpts
from flask.ext.login import current_user
from flask.ext.admin.actions import action
from wtforms.fields import SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired
from flask_wtf import Form as flask_wtf__Form
from datetime import datetime, timedelta
from botactions import update_flair


from cbbpoll import app, db
from models import User, Team, Ballot, Poll, Vote, VoterEvent, VoterApplication, ConsumptionTag

def teamChoices():
    try:
        teams = Team.query.all()
        choices = [('-1', '')]
        for team in teams:
            choice = ((team.id, str(team)))
            choices.append(choice)
    except Exception:
        choices = None
    return choices

class AdminModelView(sqla.ModelView):
    form_base_class = flask_wtf__Form
    def is_accessible(self):
        return current_user.is_admin()

class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_admin():
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class UserAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['nickname', 'email', 'emailConfirmed', 'role', 'flair_team', 'flair', 'emailReminders', 'pmReminders']
    column_list = ['id', 'nickname', 'email', 'emailConfirmed', 'role', 'is_voter', 'applicationFlag', 'flair_team.full_name']
    column_sortable_list = ('id', 'nickname', 'email','emailConfirmed', 'role', 'applicationFlag', 'flair_team.full_name')
    column_searchable_list = ('nickname', 'email')
    column_filters = ('flair_team.full_name', 'flair_team.conference', 'applicationFlag')
    form_overrides = dict(role=Select2Field)
    form_args = dict(
     #Pass the choices to the `SelectField`
        role=dict(
        choices=[('u', 'user'), ('a', 'admin')]
        ))

    @action('promote', 'Make Voter', 'Are you sure you want to grant voter status to the selected users?')
    def action_promote(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            user.is_voter = True
            db.session.add(user)
        db.session.commit()

    @action('demote', 'Revoke Voter Status', 'Are you sure you want to revoke voter status from the selected users?')
    def action_demote(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            user.is_voter = False
            db.session.add(user)
        db.session.commit()

    @action('update_flair', 'Update Flair', 'Update flair on the selected users? This may take some time and increase response time')
    def action_update_flair(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            update_flair(user)

    @action('voter_flag','Flag for Voting', 'Flag selected users for voting?')
    def action_voter_flag(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            user.applicationFlag = True
            db.session.add(user)
        db.session.commit()

    @action('voter_unflag','Unflag for Voting', 'Unflag selected users for voting?')
    def action_voter_unflag(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            user.applicationFlag = False
            db.session.add(user)
        db.session.commit()

class TeamAdmin(AdminModelView):
    column_display_pk = True
    page_size = 100
    form_columns = ['full_name', 'short_name', 'nickname', 'conference', 'flair', 'png_name']
    column_list = ['id', 'full_name', 'short_name', 'nickname', 'conference', 'flair', 'png_name']
    column_searchable_list = ('full_name', 'short_name', 'nickname', 'conference')

class PollAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['season', 'week', 'openTime', 'closeTime', 'ballots', 'redditUrl']
    column_list = ['id', 'season', 'week', 'openTime', 'closeTime', 'redditUrl']

    @action('close', 'Close Poll', 'This will snap the poll at the current time.  Continue?')
    def action_close(self, id):
        poll = Poll.query.get(id)
        poll.closeTime = datetime.utcnow()
        db.session.add(poll)
        db.session.commit()

    @action('open', 'Open Poll', 'This will cause the poll to close this time tomorrow.  Continue?')
    def action_open(self, id):
        poll = Poll.query.get(id)
        poll.closeTime = datetime.utcnow() + timedelta(days=1)
        db.session.add(poll)
        db.session.commit()

class VoteAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['ballot_id', 'rank', 'team_id', 'reason']
    column_list = ['id', 'ballot_id', 'rank', 'team_id', 'reason']
    form_overrides = dict(team_id=Select2Field)
    form_args = dict(
        team_id=dict(choices = teamChoices(),
        validators=[InputRequired(message="You must select a team.")],
        coerce=int
    ))

class BallotAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['user_id','voter', 'poll_id']
    column_list = ['id', 'voter.nickname', 'poll_id', 'updated', 'is_provisional']

class VoterEventAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['user_id', 'is_voter', 'timestamp']
    column_list = ['id', 'user_id', 'user.nickname', 'is_voter', 'timestamp']
    column_default_sort = ('timestamp', True)

class VoterApplicationAdmin(AdminModelView):
    column_display_pk = True
    column_list = ['id', 'user_id', 'user.nickname', 'primary_team', 'other_teams', 'consumption_tags']

class ConsumptionTagAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['id', 'text']
    column_list = ['id', 'text']


# Create admin
admin = admin.Admin(app, 'User Poll Control Panel', index_view=MyAdminIndexView(endpoint="admin"))
admin.add_view(UserAdmin(User, db.session))
admin.add_view(TeamAdmin(Team, db.session))
admin.add_view(PollAdmin(Poll, db.session))
admin.add_view(BallotAdmin(Ballot, db.session))
admin.add_view(VoteAdmin(Vote, db.session))
admin.add_view(VoterEventAdmin(VoterEvent, db.session))
admin.add_view(VoterApplicationAdmin(VoterApplication, db.session))
admin.add_view(ConsumptionTagAdmin(ConsumptionTag, db.session))

