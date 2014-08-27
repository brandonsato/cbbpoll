import os
import praw
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

r = praw.Reddit('/r/CollegeBasketball User Poll test')
r.set_oauth_app_info(app.config['REDDIT_CLIENT_ID'], app.config['REDDIT_CLIENT_SECRET'], app.config['REDDIT_REDIRECT_URI'])

from cbbpoll import views, models