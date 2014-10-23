from praw import Reddit
from flask import render_template, flash, redirect, session, url_for, request, g, abort, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from cbbpoll import app, db, lm, admin, message, handler
from forms import EditProfileForm, PollBallotForm, VoterApplicationForm
from models import User, Poll, Team, Ballot, Vote, VoterApplication
from datetime import datetime
from pytz import utc, timezone
from botactions import update_flair
import re
from jinja2 import evalcontextfilter, Markup, escape

eastern_tz = timezone('US/Eastern')

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

def user_by_nickname(name):
    return User.query.filter_by(nickname = name).first()

def completed_polls():
    return Poll.query.filter(Poll.has_completed == True).order_by(Poll.closeTime.desc())

def open_polls():
    return Poll.query.filter(Poll.is_open == True)

def generate_results(poll, use_provisionals=False):
    nonvoters = User.query.filter(User.was_voter_at(poll.closeTime)).all()
    results_dict = {}
    official_ballots = []
    provisional_ballots = []
    for ballot in poll.ballots:
        if ballot.is_provisional:
            provisional_ballots.append(ballot)
        else:
            official_ballots.append(ballot)
            if ballot.voter in nonvoters:
                nonvoters.remove(ballot.voter)
    counted_ballots = list(official_ballots)
    if use_provisionals:
        counted_ballots.extend(provisional_ballots)
    for ballot in counted_ballots:
        for vote in ballot.votes:
            if vote.team_id in results_dict:
                results_dict[vote.team_id][0] += 26-vote.rank
            else:
                results_dict[vote.team_id] = [26-vote.rank, 0]
            if vote.rank == 1:
                results_dict[vote.team_id][1] += 1
    results = sorted(results_dict.items(), key = lambda (k,v): (v[0],v[1]), reverse=True)
    return (results, official_ballots, provisional_ballots, nonvoters)


@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

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
    poll = completed_polls().first()
    open_poll = open_polls().first()
    results = official_ballots = provisional_ballots = nonvoters = closed_eastern = closes_eastern = None
    if poll:
        closed_eastern = poll.closeTime.replace(tzinfo=utc).astimezone(eastern_tz)
        (results, official_ballots, provisional_ballots, nonvoters) = generate_results(poll)
    if open_poll:
        closes_eastern = open_poll.closeTime.replace(tzinfo=utc).astimezone(eastern_tz)
    return render_template('index.html',
        title = 'Home',
        results = results,
        user = user,
        poll = poll,
        official_ballots = official_ballots,
        provisional_ballots = provisional_ballots,
        users = User.query,
        teams=Team.query,
        closed_eastern = closed_eastern,
        nonvoters=nonvoters,
        open_poll = open_poll,
        closes_eastern = closes_eastern
        )

@app.route('/authorize_callback', methods = ['GET', 'POST'])
def authorized():
    reddit_state = request.args.get('state', '')
    reddit_code = request.args.get('code', '')
    if not reddit_state or not reddit_code:
        return redirect(url_for('index'))
    r = Reddit(app.config['REDDIT_USER_AGENT'], handler=handler)
    r.set_oauth_app_info(app.config['REDDIT_CLIENT_ID'], app.config['REDDIT_CLIENT_SECRET'], app.config['REDDIT_REDIRECT_URI'])
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
    update_flair(user)
    return redirect(next_path or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    flash ('Successfully Logged Out', 'success')
    return redirect(url_for('index'))

@app.route('/login')
def login():
    next = request.args.get('next')
    from uuid import uuid1
    state = str(uuid1())
    session['oauth_state'] = state
    session['last_path'] = next
    r = Reddit(app.config['REDDIT_USER_AGENT'], handler=handler)
    r.set_oauth_app_info(app.config['REDDIT_CLIENT_ID'], app.config['REDDIT_CLIENT_SECRET'], app.config['REDDIT_REDIRECT_URI'])
    authorize_url = r.get_authorize_url(state,refreshable=True)
    return redirect(authorize_url)


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/')
@app.route('/user/<nickname>/<int:page>')
@app.route('/user/<nickname>/<int:page>/')
def user(nickname, page=1):
    user = user_by_nickname(nickname)
    if user == None:
        flash('User ' + nickname + ' not found.', 'warning')
        return redirect(url_for('index'))
    ballots = user.ballots.filter(Poll.has_completed == True)
    application = VoterApplication.query.filter_by(user_id=user.id).first()
    if user == g.user or g.user.is_admin():
        pending_ballot = user.ballots.filter(Poll.has_completed == False).first()
        if pending_ballot:
            ballots = user.ballots
    ballots = ballots.join(Poll, Ballot.fullpoll).order_by(Poll.closeTime.desc())
    return render_template('user.html', ballots = ballots.paginate(page,10,False),
        user = user, application = application)

@app.route('/editprofile', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditProfileForm()
    if form.validate_on_submit():
        g.user.emailReminders = form.emailReminders.data
        g.user.pmReminders = form.pmReminders.data
        if not form.email.data:
            g.user.email = None
            g.user.emailConfirmed = None
            db.session.add(g.user)
            db.session.commit()
            flash('Profile Successfully Updated.', 'info')
            return redirect(url_for('edit'))
        if form.email.data == g.user.email and g.user.emailConfirmed:
            db.session.add(g.user)
            db.session.commit()
            flash('Profile Successfully Updated.', 'info')
            return redirect(url_for('edit'))
        provisionalEmail = form.email.data
        if g.user.email is None or g.user.emailConfirmed == False:
            g.user.email = provisionalEmail
            g.user.emailConfirmed = False
            db.session.add(g.user)
            db.session.commit()
        message.send_email('Confirm Your Account', [provisionalEmail], 'confirmation',
            user=g.user, token=g.user.generate_confirmation_token(email=provisionalEmail))
        flash('Please check your email for a confirmation message.', 'warning')
        return redirect(url_for('edit'))

    form.email.data = g.user.email
    form.emailReminders.data = g.user.emailReminders
    form.pmReminders.data = g.user.pmReminders
    return render_template('editprofile.html',
        form = form, user = g.user)

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
    message.send_email('Confirm Your Account', [current_user], 'confirmation', token=token)
    flash('A new confirmation email has been sent to you.', 'info')
    return redirect(url_for('index'))

@app.route('/teams')
def teams():
    teams = Team.query.all()
    return render_template('teams.html',
        teams=teams)

@app.route('/submitballot', methods = ['GET', 'POST'])
@login_required
def submitballot():
    poll = open_polls().first()
    if not poll:
        flash('No open polls', 'info')
        return redirect(url_for('index'))
    ballot = Ballot.query.filter_by(poll_id = poll.id).filter_by(user_id = g.user.id).first()
    teams = Team.query.all()
    voter = current_user.is_voter
    editing = bool(ballot)
    closes_eastern = poll.closeTime.replace(tzinfo=utc).astimezone(eastern_tz)
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
        else:
            ballot = Ballot(updated = datetime.utcnow(), poll_id = poll.id, user_id = g.user.id)
        db.session.add(ballot)
        # must commit to get ballot id
        db.session.commit()
        for voteRank, vote in enumerate(form.votes):
            voteModel = Vote(ballot_id=ballot.id, team_id = vote.team.data.id, rank = (voteRank+1), reason = vote.reason.data)
            db.session.add(voteModel)
        db.session.commit()
        flash('Ballot submitted.', 'success')
        return redirect(url_for('ballot', ballot_id=ballot.id))
    return render_template('submitballot.html',
      teams=teams, form=form, poll=poll,
      is_provisional = not voter, editing = editing, closes_eastern = closes_eastern)

@app.route('/poll/<int:s>/<int:w>', methods = ['GET', 'POST'])
def polls(s, w):
    prov = request.args.get('prov', False)
    poll = Poll.query.filter_by(season=s).filter_by(week=w).first()
    if not poll:
        flash('No such poll', 'warning')
        return redirect(url_for('index'))
    closes_eastern = poll.closeTime.replace(tzinfo=utc).astimezone(eastern_tz)
    if not poll.has_completed and not current_user.is_admin():
        flash('Poll has not yet completed. Please wait until '+ closes_eastern.strftime('%A, %B %-d, %Y at %-I:%M%p %Z'), 'warning')
        return redirect(url_for('index'))
    (results, official_ballots, provisional_ballots,nonvoters) = generate_results(poll, prov)
    return render_template('polldetail.html',
        season=s, week=w, poll=poll, results=results, official_ballots = official_ballots,
        provisional_ballots = provisional_ballots, users = User.query,
        teams = Team.query, closes_eastern = closes_eastern, prov=prov, nonvoters=nonvoters)


@app.route('/results')
@app.route('/results/')
@app.route('/results/<int:page>/')
@app.route('/results/<int:page>')
def results(page=1):
    prov = request.args.get('prov', False)
    polls = completed_polls().paginate(page, 1, False)
    poll = None
    if polls.items:
        poll = polls.items[0]
    if not poll:
        if page == 1:
            flash('No polls have been completed yet.  Check back soon!', 'info')
        else:
            flash(page + 'No such poll', 'warning')
        return redirect(url_for('index'))
    closes_eastern = poll.closeTime.replace(tzinfo=utc).astimezone(eastern_tz)
    if not poll.has_completed and not current_user.is_admin():
        flash('Poll has not yet completed. Please wait until '+ closes_eastern.strftime('%A, %B %-d, %Y at %-I:%M%p %Z'), 'warning')
        return redirect(url_for('index'))
    (results, official_ballots, provisional_ballots, nonvoters) = generate_results(poll, prov)

    return render_template('results.html',
        season=poll.season, week=poll.week, polls=polls, poll=poll,
        official_ballots = official_ballots, provisional_ballots = provisional_ballots, page=page, results=results,
        users = User.query, teams=Team.query, closes_eastern = closes_eastern, prov=prov, nonvoters=nonvoters)

@app.route('/ballot/<int:ballot_id>/')
@app.route('/ballot/<int:ballot_id>')
def ballot(ballot_id):
    ballot = Ballot.query.get(ballot_id)
    if not ballot:
        flash('No such ballot', 'warning')
        return redirect(url_for('index'))
    poll = Poll.query.get(ballot.poll_id)
    closes_eastern = poll.closeTime.replace(tzinfo=utc).astimezone(eastern_tz)
    updated_eastern = ballot.updated.replace(tzinfo=utc).astimezone(eastern_tz)
    if not poll.has_completed and not current_user.is_admin() and current_user != ballot.voter:
        flash('Poll has not yet completed. Please wait until '+ closes_eastern.strftime('%A, %B %-d, %Y at %-I:%M%p %Z'), 'warning')
        return redirect(url_for('index'))
    votes = []
    for vote in ballot.votes:
        votes.append({'rank':vote.rank, 'team':vote.team_id, 'reason':vote.reason})
    votes.sort(key=lambda vote: vote['rank'])
    return render_template('ballot.html', ballot=ballot, votes=votes,
        teams=Team.query, updated_eastern = updated_eastern)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/voters')
def voters():
    users = User.query
    voters = users.filter(User.is_voter==True)
    return render_template('voters.html', users = users, voters=voters)

@app.route('/apply', methods = ['GET', 'POST'])
@login_required
def apply():
    application = VoterApplication.query.filter_by(user_id=g.user.id).first()
    if application:
        flash("Application Already Submitted", 'info')
        return redirect(url_for('index'))
    form = VoterApplicationForm()
    if form.validate_on_submit():
        application=VoterApplication(
        user_id = g.user.id,
        primary_team_id = form.primary_team_id.data.id,
        approach = form.approach.data,
        other_comments = form.other_comments.data,
        will_participate = form.will_participate.data,
        updated = datetime.utcnow()
        )
        for team in form.data['other_teams']:
            application.other_teams.append(team)
        for tag in form.data['consumption_tags']:
            application.consumption_tags.append(tag)
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!','success')
        return redirect(url_for('user', nickname=g.user.nickname))
    return render_template('apply.html', form = form)

@app.route('/applications')
def applications():
    if not current_user.is_admin():
        abort(403)
    applications = VoterApplication.query.all()
    return render_template('applications.html', applications = applications)

@app.route('/users')
def users():
    if not current_user.is_admin():
        abort(403)
    users = User.query
    return render_template('users.html', users = users)

@app.route('/_flag_user')
def _flag_user():
    if not current_user.is_admin():
        abort(403)
    id = request.args.get('id', False)
    if id:
        user=User.query.get(id)
        if user:
            flag = not user.applicationFlag
            user.applicationFlag = flag
            db.session.add(user)
            db.session.commit()
            return jsonify(flagged=flag)
    return jsonify()
