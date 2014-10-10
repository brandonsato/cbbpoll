import os
import praw
from flask import Flask
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.migrate import Migrate, MigrateCommand
from praw.handlers import MultiprocessHandler

# handler needs to be started separately by running praw-multiprocess
# this allows the handler to adhere to rate limit of reddit API
# see r and bot below to enable in production.

handler = MultiprocessHandler()

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_message = None
mail = Mail(app)
Bootstrap(app)
lm.login_view = 'login'
migrate = Migrate(app, db)

r = praw.Reddit(app.config['REDDIT_USER_AGENT'], handler=handler)
r.set_oauth_app_info(app.config['REDDIT_CLIENT_ID'], app.config['REDDIT_CLIENT_SECRET'], app.config['REDDIT_REDIRECT_URI'])
bot = praw.Reddit(app.config['REDDIT_USER_AGENT'], handler=handler)
bot.login(app.config['REDDIT_USERNAME'], app.config['REDDIT_PASSWORD'])

from cbbpoll import views, models, admin
lm.anonymous_user = models.AnonymousUser

