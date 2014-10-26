# Modify these values for your app and environment and rename to config.py
# Don't track changes to this file for security purposes.

CSRF_ENABLED = True
SECRET_KEY = 'Hard to guess!'

# Debug allows arbitrary execution of code by people who can
# access the site--for dev environments only.
DEBUG = True

REDDIT_CLIENT_ID = "From Reddit"
REDDIT_CLIENT_SECRET = "Also from Reddit... DO NOT SHARE"
REDDIT_REDIRECT_URI = "localhost:5000/authorize_callback"
REDDIT_USER_AGENT = '/r/CollegeBasketball User Poll'

REDDIT_USERNAME = 'bot_name'
REDDIT_PASSWORD = 'bot_password'

SQLALCHEMY_DATABASE_URI = 'mysql://username:password@mysql.server/dbname'

# for pythonanywhere deployment
SQLALCHEMY_POOL_RECYCLE = 499
SQLALCHEMY_POOL_TIMEOUT = 20

LOGFILE = 'logfile.txt'

# email server
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'gmail-username'
MAIL_PASSWORD = 'gmail-password'
MAIL_FROM = 'from.address@example.com'
