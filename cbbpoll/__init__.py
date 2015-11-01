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

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(app.config['LOGFILE'], maxBytes = 1024*1024)
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

bot = praw.Reddit(app.config['REDDIT_USER_AGENT'], handler=handler)
bot.login(app.config['REDDIT_USERNAME'], app.config['REDDIT_PASSWORD'], disable_warning=True)

from cbbpoll import views, models, admin
lm.anonymous_user = models.AnonymousUser
app.jinja_env.globals['timestamp'] = views.timestamp

