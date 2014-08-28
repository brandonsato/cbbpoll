from cbbpoll import db

ROLE_USER = 0
ROLE_POLLSTER = 1
ROLE_ADMIN = 5

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(20), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    accessToken = db.Column(db.String(30))
    refreshToken = db.Column(db.String(30))
    refreshAfter = db.Column(db.DateTime)
    ballots = db.relationship('Ballot', backref = 'pollster', lazy = 'joined')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Poll(db.Model):
    __tablename__ = 'poll'
    id = db.Column(db.Integer, primary_key = True)
    season = db.Column(db.Integer)
    week = db.Column(db.Integer)
    openTime = db.Column(db.DateTime)
    closeTime = db.Column(db.DateTime)
    results = db.relationship('Result', backref = 'fullpoll', lazy = 'joined')
    ballots = db.relationship('Ballot', backref = 'fullpoll', lazy = 'joined')


    def __repr__(self):
        return '<Poll Week %r of %r>' % (self.week, self.season)

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String(75))
    short_name = db.Column(db.String(50))
    flair = db.Column(db.String(50))
    nickname = db.Column(db.String(50))
    conference = db.Column(db.String(50))

    def __repr__(self):
        return '<Team %r>' % (self.short_name)

class Ballot(db.Model):
    __tablename__ = 'ballot'
    id = db.Column(db.Integer, primary_key = True)
    updated = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    votes = db.relationship('Vote', backref = 'fullballot', lazy = 'joined')


    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Vote(db.Model):
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key = True)
    ballot_id = db.Column(db.Integer, db.ForeignKey('ballot.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    rank = db.Column(db.SmallInteger)
    reason = db.Column(db.String(140))

    def __repr__(self):
        return '<Vote %r on Ballot %r>' % (self.rank, self.ballot_id)

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key = True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    score = db.Column(db.Integer)

    def __repr__(self):
        return '<Result %r for team %r on Poll %r>' % (self.id, self.team_id, self.poll)





