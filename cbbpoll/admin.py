from flask import redirect, url_for, flash
from flask.ext import admin
from flask.ext.admin import expose
from flask.ext.admin.contrib import sqla
from flask.ext.admin.form.fields import Select2Field
from flask.ext.admin.form import FormOpts
from flask.ext.login import current_user
from wtforms.fields import SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required, InputRequired, Length
from flask_wtf import Form as flask_wtf__Form


from cbbpoll import app, db
from models import User, Team, Ballot, Poll, Result, Vote

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
        return not current_user.is_anonymous() and current_user.is_admin()

class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if current_user.is_anonymous() or not current_user.is_admin():
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class UserAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['nickname', 'email', 'emailConfirmed', 'role']
    column_list = ['id', 'nickname', 'email', 'emailConfirmed', 'role']
    column_searchable_list = ('nickname', 'email')
    form_overrides = dict(role=Select2Field)
    form_args = dict(
     #Pass the choices to the `SelectField`
        role=dict(
        choices=[('u', 'user'), ('p', 'pollster'), ('a', 'admin')]
        ))

class TeamAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['full_name', 'short_name', 'nickname', 'conference', 'flair']
    column_list = ['id', 'full_name', 'short_name', 'nickname', 'conference', 'flair']
    column_searchable_list = ('full_name', 'short_name', 'nickname', 'conference')

class PollAdmin(AdminModelView):
        column_display_pk = True
        form_columns = ['season', 'week', 'openTime', 'closeTime', 'ballots', 'results']
        column_list = ['id', 'season', 'week', 'openTime', 'closeTime', 'ballots', 'results']

class ResultAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['poll_id', 'team_id', 'score', 'onevotes']
    column_list = ['id', 'poll_id', 'team_id', 'score', 'onevotes']
    form_overrides = dict(team_id=Select2Field)
    form_args = dict(
        team_id=dict(choices = teamChoices(),
        validators=[InputRequired(message="You must select a team.")],
        coerce=int
        ))

class VoteAdmin(AdminModelView):
        column_display_pk = True
        form_columns = ['ballot_id', 'rank', 'team_id', 'reason']
        column_list = ['id', 'ballot_id', 'rank', 'team_id', 'reason']

class BallotAdmin(AdminModelView):
        column_display_pk = True
        form_columns = ['user_id', 'poll_id']
        column_list = ['id', 'user_id', 'poll_id', 'updated', 'votes']





# Create admin
admin = admin.Admin(app, 'User Poll Control Panel', index_view=MyAdminIndexView(endpoint="admin"))
admin.add_view(UserAdmin(User, db.session))
admin.add_view(TeamAdmin(Team, db.session))
admin.add_view(PollAdmin(Poll, db.session))
admin.add_view(ResultAdmin(Result, db.session))
admin.add_view(BallotAdmin(Ballot, db.session))
admin.add_view(VoteAdmin(Vote, db.session))

