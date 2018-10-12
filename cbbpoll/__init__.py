from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import praw


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
    file_handler = RotatingFileHandler(app.config['LOGFILE'], maxBytes=(1024*1024))
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

bot = praw.Reddit(
    client_id=app.config['BOT_REDDIT_CLIENT_ID'],
    client_secret=app.config['BOT_REDDIT_CLIENT_SECRET'],
    username=app.config['BOT_REDDIT_USERNAME'],
    password=app.config['BOT_REDDIT_PASSWORD'],
    user_agent=app.config['BOT_REDDIT_USER_AGENT'],
    )

from cbbpoll import views, models, admin
lm.anonymous_user = models.AnonymousUser
app.jinja_env.globals['timestamp'] = views.timestamp

