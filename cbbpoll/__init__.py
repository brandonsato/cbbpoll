import os
import praw
from flask import Flask
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
mail = Mail(app)
Bootstrap(app)
lm.login_view = 'login'
migrate = Migrate(app, db)

r = praw.Reddit(app.config['REDDIT_USER_AGENT'])
r.set_oauth_app_info(app.config['REDDIT_CLIENT_ID'], app.config['REDDIT_CLIENT_SECRET'], app.config['REDDIT_REDIRECT_URI'])

from cbbpoll import views, models, admin
