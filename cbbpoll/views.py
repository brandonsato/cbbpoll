from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from cbbpoll import app, db, lm, r
from forms import LoginForm
from models import User, ROLE_USER, ROLE_POLLSTER, ROLE_ADMIN

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
@login_required
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
    link_refresh = r.get_authorize_url('DifferentUniqueKey',
                                       refreshable=True)
    link_refresh = "<a href=%s>link</a>" % link_refresh
    text = "Login with Reddit %s</br></br>" % link_refresh
    return text


@app.route('/authorize_callback', methods = ['GET', 'POST'])
def authorized():
    reddit_state = request.args.get('state', '')
    reddit_code = request.args.get('code', '')
    reddit_info = r.get_access_information(reddit_code)
    reddit_user = r.get_me()


    user = User.query.filter_by(nickname = reddit_user.name).first()
    if user is None:
      nickname = reddit_user.name
      user = User(nickname = nickname, role = ROLE_USER, accessToken = reddit_info['access_token'], refreshToken = reddit_info['refresh_token'])
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

