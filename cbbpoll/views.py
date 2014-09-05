from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from cbbpoll import app, db, lm, r, admin
from forms import LoginForm, EditProfileForm, PollBallotForm
from models import User, Poll, Team, Ballot, Vote, Result
from datetime import datetime

def user_by_nickname(name):
    return User.query.filter_by(nickname = name).first()

def completed_polls():
    return Poll.query.filter(Poll.closeTime < datetime.now()).order_by(Poll.closeTime.desc())

def open_polls():
    return Poll.query.filter(Poll.closeTime > datetime.now()).filter(Poll.openTime < datetime.now())


@app.before_request
def before_request():
    g.authorize_url = r.get_authorize_url('cbbloginkey',refreshable=True)
    g.user = current_user
    if g.user.is_authenticated():
        db.session.add(g.user)
        db.session.commit()

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', authorize_url=g.authorize_url), 404

@app.errorhandler(500)
def internal_error(error):
    authorize_url = g.authorize_url
    db.session.rollback()
    return render_template('500.html', authorize_url=authorize_url), 500

@app.route('/')
def index():
    user = g.user
    return render_template('index.html',
        title = 'Home',
        user = user,
        authorize_url=g.authorize_url)

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html',
      form = form,
      title = "Login or Sign Up",
      authorize_url=g.authorize_url)


@app.route('/authorize_callback', methods = ['GET', 'POST'])
def authorized():
    reddit_state = request.args.get('state', '')
    reddit_code = request.args.get('code', '')
    reddit_info = r.get_access_information(reddit_code)
    reddit_user = r.get_me()
    user = user_by_nickname(reddit_user.name)
    if user is None:
        nickname = reddit_user.name
        user = User(nickname = nickname, role = 'u', accessToken = reddit_info['access_token'], refreshToken = reddit_info['refresh_token'])
    else:
        user.accessToken = reddit_info['access_token']
        user.refreshToken = reddit_info['refresh_token']
    db.session.add(user)
    db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/<nickname>')
def user(nickname):
    user = user_by_nickname(nickname)
    if user == None:
        flash('User ' + nickname + ' not found.', 'warning')
        return redirect(url_for('index'))
    return render_template('user.html',
        user = user, authorize_url = g.authorize_url)

@app.route('/editprofile', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditProfileForm()
    if form.validate_on_submit():
        g.user.email = form.email.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.', 'info')
        return redirect(url_for('edit'))
    else:
        form.email.data = g.user.email
    return render_template('editprofile.html',
        form = form, authorize_url = g.authorize_url)

@app.route('/teams')
def teams():
    teams = Team.query.all()
    return render_template('teams.html', 
      teams=teams, authorize_url = g.authorize_url)

@app.route('/submitballot', methods = ['GET', 'POST'])
@login_required
def submitballot():
    poll = open_polls().first()
    if not poll:
        flash('No open polls', 'info')
        return redirect(url_for('index'))
    ballot = Ballot.query.filter_by(poll_id = poll.id).filter_by(user_id = g.user.id).first()
    if ballot:
        flash('Ballot already submitted to this poll', 'warning')
        return redirect(url_for('index'))
    teams = Team.query.all()
    form = PollBallotForm()
    if form.validate_on_submit():
        ballot = Ballot(updated = datetime.now(), poll_id = poll.id, user_id = g.user.id)
        db.session.add(ballot)
        db.session.commit()
        flash('Ballot submitted.', 'success')
        return redirect(url_for('index'))
    return render_template('submitballot.html', 
      teams=teams, form=form, authorize_url = g.authorize_url, poll=poll)

@app.route('/poll/<int:s>/<int:w>')
def results(s, w):
    poll = Poll.query.filter_by(season=s).filter_by(week=w).first();
    if not poll:
        flash('No such poll', 'warning')
        return redirect(url_for('index'))
    elif not poll.has_completed:
        flash('Poll has not yet completed. Please wait until '+ str(poll.closeTime), 'warning')
        return redirect(url_for('index'))
    return render_template('results.html', 
      season=s, week=w, poll=poll, teams = Team.query, authorize_url = g.authorize_url)

@app.route('/results')
@app.route('/results/')
@app.route('/results/<int:page>')
def polls(page=1):
    polls = completed_polls().paginate(page, 1, False).items;
    poll = polls[page-1]
    if not poll:
        flash('No such poll', 'warning')
        return redirect(url_for('index'))
    elif not poll.has_completed:
        flash('Poll has not yet completed. Please wait until '+ str(poll.closeTime), 'warning')
        return redirect(url_for('index'))
    return render_template('results.html', 
      season=poll.season, week=poll.week, polls=polls, poll=poll, page=page, teams=Team.query, authorize_url = g.authorize_url)



