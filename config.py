# Modify these values for your app and environment.
# Don't track changes to this file for security purposes. 

CSRF_ENABLED = True
SECRET_KEY = 'Hard to guess!'

REDDIT_CLIENT_ID = "From Reddit"
REDDIT_CLIENT_SECRET = "DO NOT SHARE"
REDDIT_REDIRECT_URI = "localhost:5000/reddit_callback"

SQLALCHEMY_DATABASE_URI = 'mysql://username:password@mysql.server/dbname'

ROLE_USER = 0
ROLE_POLLSTER = 2
ROLE_ADMIN = 5