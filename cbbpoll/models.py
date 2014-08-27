from cbbpoll import db

ROLE_USER = 0
ROLE_POLLSTER = 1
ROLE_ADMIN = 5

class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(20), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    accessToken = db.Column(db.String(30))
    refreshToken = db.Column(db.string(30))
    refreshAfter = db.Column(db.datetime)

    def __repr__(self):
        return '<User %r>' % (self.nickname)