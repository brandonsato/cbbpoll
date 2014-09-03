from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from cbbpoll import app, db, lm, r
from forms import LoginForm, EditProfileForm, PollBallotForm
from models import User, Poll, Team, Ballot, Vote, Result

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        db.session.add(g.user)
        db.session.commit()

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/')
def index():
    user = g.user
    return render_template('index.html',
        title = 'Home',
        user = user)

@app.route('/login')
def login():
    form = LoginForm()
    authorize_url = r.get_authorize_url('cbbloginkey',refreshable=True)
    return render_template('login.html',
      form = form,
      title = "Login or Sign Up",
      authorize_url = authorize_url)


@app.route('/authorize_callback', methods = ['GET', 'POST'])
def authorized():
    reddit_state = request.args.get('state', '')
    reddit_code = request.args.get('code', '')
    reddit_info = r.get_access_information(reddit_code)
    reddit_user = r.get_me()
    user = User.query.filter_by(nickname = reddit_user.name).first()
    if user is None:
      nickname = reddit_user.name
      user = User(nickname = nickname, role = 'u', accessToken = reddit_info['access_token'], refreshToken = reddit_info['refresh_token'])
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
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.', 'warning')
        return redirect(url_for('index'))
    return render_template('user.html',
        user = user)

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
        form = form)

@app.route('/teams')
def teams():
    teams = Team.query.all()
    return render_template('teams.html', teams=teams)

@app.route('/submitballot', methods = ['GET', 'POST'])
def submitballot():
    teams = Team.query.all()
    form = PollBallotForm()
    if form.validate_on_submit():
        flash('Ballot submitted.', 'success')
        flash(form.votes[1], 'warning')
        return redirect(url_for('index'))

    return render_template('submitballot.html', teams=teams, form=form)

@app.route('/poll/<s>/<w>')
def results(s, w):
    poll = Poll.query.filter_by(season=s).filter_by(week=w).first();
    if not poll:
        flash('No such poll', 'warning')
        return redirect(url_for('index'))
    elif not poll.has_completed:
        flash('Poll has not yet completed. Please wait until '+ str(poll.closeTime), 'warning')
        return redirect(url_for('index'))
    return render_template('results.html', season=s, week=w, poll=poll, teams = Team.query)


