from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from cbbpoll import app, db, lm, r
from forms import LoginForm, EditProfileForm, AdminProfileForm
from models import User, Poll, Team, Ballot, Vote, Result

@app.before_request
def before_request():
    g.user = current_user
    logged_in = getattr(g, "user", None)

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

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
@app.route('/index')
def index():
    user = g.user
    posts = [
        { 
            'author': { 'nickname': 'John' }, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': { 'nickname': 'Susan' }, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template('index.html',
        title = 'Home',
        user = user,
        posts = posts)

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
      user = User(nickname = nickname, role = app.config['ROLE_USER'], accessToken = reddit_info['access_token'], refreshToken = reddit_info['refresh_token'])
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
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    posts = [
        { 'author': user, 'body': 'Test post #1' },
        { 'author': user, 'body': 'Test post #2' }
    ]
    return render_template('user.html',
        user = user,
        posts = posts)

@app.route('/editprofile', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditProfileForm()
    if form.validate_on_submit():
        g.user.email = form.email.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.email.data = g.user.email
    return render_template('editprofile.html',
        form = form)

@app.route('/adminprofile/<nickname>', methods = ['GET', 'POST'])
@login_required
def admin(nickname):
    if not g.user.is_admin():
        return redirect(url_for('index'))
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    form = AdminProfileForm()
    if form.validate_on_submit():
        user.email = form.email.data
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash("Admin changes have been saved.")
        return redirect(url_for('admin', nickname = nickname))
    else:
        form.email.data = user.email
        form.role.data = user.role
    return render_template('adminprofile.html',
        user = user,
        form = form)

@app.route('/teams')
def teams():
    teams = Team.query.all()
    return render_template('teams.html', teams = teams)


