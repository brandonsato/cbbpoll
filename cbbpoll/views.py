from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from cbbpoll import app, db, lm, r, admin, email
from forms import EditProfileForm, PollBallotForm, EmailReminderForm
from models import User, Poll, Team, Ballot, Vote
from datetime import datetime

def user_by_nickname(name):
    return User.query.filter_by(nickname = name).first()

def completed_polls():
    return Poll.query.filter(Poll.closeTime < datetime.now()).order_by(Poll.closeTime.desc())

def open_polls():
    return Poll.query.filter(Poll.closeTime > datetime.now()).filter(Poll.openTime < datetime.now())

def generate_results(poll, use_provisionals=False):
    results_dict = {}
    official_ballots = []
    provisional_ballots = []
    for ballot in poll.ballots:
        if ballot.is_provisional:
            provisional_ballots.append(ballot)
        else:
            official_ballots.append(ballot)
    counted_ballots = list(official_ballots)
    if use_provisionals:
        official_ballots.extend(provisional_ballots)
    for ballot in counted_ballots:
        for vote in ballot.votes:
            if vote.team_id in results_dict:
                results_dict[vote.team_id][0] += 26-vote.rank
            else:
                results_dict[vote.team_id] = [26-vote.rank, 0]
            if vote.rank == 1:
                results_dict[vote.team_id][1] += 1
    results = sorted(results_dict.items(), key = lambda (k,v): (v[0],v[1]), reverse=True)
    return (results, official_ballots, provisional_ballots)


@app.before_request
def before_request():
    # prevent generating multiple oauth states per page load
    if request.endpoint != 'static':
        g.user = current_user
        # don't need an authorize_url if the user is logged in
        # but must be initialized for passing to render_template
        if g.user.is_authenticated():
            db.session.add(g.user)
            db.session.commit()
            g.authorize_url = ''
        elif request.endpoint != 'authorized':
            from uuid import uuid1
            state = str(uuid1())
            session['oauth_state'] = state
            session['last_path'] = request.path
            g.authorize_url = r.get_authorize_url(state,refreshable=True)


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
    poll = completed_polls().first()
    return render_template('index.html',
        title = 'Home',
        user = user,
        poll = poll,
        authorize_url=g.authorize_url,
        teams=Team.query)

@app.route('/authorize_callback', methods = ['GET', 'POST'])
def authorized():
    reddit_state = request.args.get('state', '')
    reddit_code = request.args.get('code', '')
    reddit_info = r.get_access_information(reddit_code)
    reddit_user = r.get_me()
    next_path = session['last_path']
    if reddit_state != session['oauth_state']:
        flash("Invalid state given, please try again.", 'danger')
        return redirect(next_path or url_for('index'))
    user = user_by_nickname(reddit_user.name)
    if user is None:
        nickname = reddit_user.name
        user = User(nickname = nickname, role = 'u',
            accessToken = reddit_info['access_token'],
            refreshToken = reddit_info['refresh_token'])
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
    return redirect(next_path or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    flash ('Successfully Logged Out', 'success')
    return redirect(url_for('index'))

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@app.route('/user/<nickname>/<int:page>/')
def user(nickname, page=1):
    user = user_by_nickname(nickname)
    if user == None:
        flash('User ' + nickname + ' not found.', 'warning')
        return redirect(url_for('index'))
    return render_template('user.html', ballots = user.ballots.paginate(page,10,False),
        user = user, authorize_url = g.authorize_url)

@app.route('/editprofile', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditProfileForm()
    if form.validate_on_submit():
        if not form.email.data:
            g.user.email = None;
            g.user.emailConfirmed = None;
            db.session.add(g.user)
            db.session.commit()
            flash('Email address successfully cleared from profile.', 'info')
            return redirect(url_for('index'))
        if form.email.data == g.user.email:
            return redirect(url_for('edit'))
        provisionalEmail = form.email.data
        if g.user.email is None or g.user.emailConfirmed == False:
            g.user.email = provisionalEmail
            g.user.emailConfirmed = False
            db.session.add(g.user)
            db.session.commit()
        email.send_email('Confirm Your Account', [provisionalEmail], 'confirmation',
            user=g.user, token=g.user.generate_confirmation_token(email=provisionalEmail))
        flash('Please check your email for a confirmation message.', 'warning')
        return redirect(url_for('index'))

    form.email.data = g.user.email
    return render_template('editprofile.html',
        form = form, authorize_url = g.authorize_url)

@app.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirm(token):
        print(current_user.email)
        flash('You have successfully confirmed your email address.  Thanks!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('index'))

@app.route('/confirm')
@login_required
def retry_confirm():
    if current_user.emailConfirmed:
        flash('Your email address has been confirmed.', 'success')
        return redirect(url_for('index'))
    token = current_user.generate_confirmation_token()
    email.send_email('Confirm Your Account', [current_user], 'confirmation', token=token)
    flash('A new confirmation email has been sent to you.', 'info')
    return redirect(url_for('index'))

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
    teams = Team.query.all()
    pollster = current_user.is_pollster()
    editing = bool(ballot)
    if ballot:
        vote_dicts = [{} for i in range(25)]
        for vote in ballot.votes:
            vote_index = vote.rank-1
            vote_dicts[vote_index]['team'] = Team.query.get(vote.team_id)
            vote_dicts[vote_index]['reason'] = vote.reason
        data_in = {'votes': vote_dicts}
        form = PollBallotForm(data = data_in)
    else:
        form = PollBallotForm()

    if form.validate_on_submit():
        if ballot:
            for vote in ballot.votes:
                db.session.delete(vote)
            ballot.updated = datetime.utcnow()
            ballot.is_provisional = not pollster
        else:
            ballot = Ballot(updated = datetime.utcnow(), poll_id = poll.id, user_id = g.user.id, 
            is_provisional = not pollster)
        db.session.add(ballot)
        # must commit to get ballot id
        db.session.commit()
        for voteRank, vote in enumerate(form.votes):
            voteModel = Vote(ballot_id=ballot.id, team_id = vote.team.data.id, rank = (voteRank+1), reason = vote.reason.data)
            db.session.add(voteModel)
        db.session.commit()
        flash('Ballot submitted.', 'success')
        return redirect(url_for('index'))
    return render_template('submitballot.html', 
      teams=teams, form=form, authorize_url = g.authorize_url, poll=poll, 
      is_provisional = not pollster, editing = editing)

@app.route('/poll/<int:s>/<int:w>', methods = ['GET', 'POST'])
def results(s, w):
    poll = Poll.query.filter_by(season=s).filter_by(week=w).first();
    if not poll:
        flash('No such poll', 'warning')
        return redirect(url_for('index'))
    elif not poll.has_completed and not current_user.is_admin():
        flash('Poll has not yet completed!', 'warning')
    (results, official_ballots, provisional_ballots) = generate_results(poll)

    return render_template('polldetail.html', 
        season=s, week=w, poll=poll, results=results, official_ballots = official_ballots, 
        provisional_ballots = provisional_ballots, users = User.query, 
        teams = Team.query, authorize_url = g.authorize_url)


@app.route('/results')
@app.route('/results/')
@app.route('/results/<int:page>/')
@app.route('/results/<int:page>')
def polls(page=1):
    polls = completed_polls().paginate(page, 1, False).items;
    poll = polls[page-1]
    if not poll:
        flash('No such poll', 'warning')
        return redirect(url_for('index'))
    elif not poll.has_completed and not current_user.is_admin():
        flash('Poll has not yet completed. Please wait until '+ str(poll.closeTime), 'warning')
        return redirect(url_for('index'))
    (results, official_ballots, provisional_ballots) = generate_results(poll)

    return render_template('results.html', 
        season=poll.season, week=poll.week, polls=polls, poll=poll, 
        official_ballots = official_ballots, page=page, results=results, 
        users = User.query, teams=Team.query, authorize_url = g.authorize_url)

@app.route('/ballot/<int:ballot_id>/')
@app.route('/ballot/<int:ballot_id>')
def ballot(ballot_id):
    ballot = Ballot.query.get(ballot_id)
    if not ballot:
        flash('No such ballot', 'warning')
        return redirect(url_for('index'))
    poll = Poll.query.get(ballot.poll_id)
    if not poll.has_completed() and not current_user.is_admin():
        flash('Poll has not yet completed. Please wait until '+ str(poll.closeTime), 'warning')
        return redirect(url_for('index'))
    votes = []
    for vote in ballot.votes:
        votes.append({'rank':vote.rank, 'team':vote.team_id, 'reason':vote.reason})
    votes.sort(key=lambda vote: vote['rank'])
    return render_template('ballot.html', ballot=ballot, votes=votes,
        teams=Team.query, authorize_url=g.authorize_url)


