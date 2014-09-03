import datetime
from cbbpoll import db, app

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(20), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.Enum('u','p','a'), default = 'u')
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

    def is_admin(self):
        return self.role == 'a'

    def is_pollster(self):
        return self.role == 'p' or self.role == 'a'

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
    results = db.relationship('Result', backref = 'fullpoll', lazy = 'joined', order_by="desc(Result.score)")
    ballots = db.relationship('Ballot', backref = 'fullpoll', lazy = 'joined')

    def is_open(self):
        return (datetime.now > self.openTime and datetime.now < self.closeTime)

    def has_completed(self):
        return datetime.now > self.closeTime


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

    def __str__(self):
        s = self.full_name
        if self.short_name:
            s = "".join([self.short_name, " (", s, ")"])
        return s

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
    onevotes = db.Column(db.Integer)

    def __repr__(self):
        return '<Result %r for Poll %r: %r %r points>' % (self.id, self.poll_id, Team.query.get(self.team_id).flair, self.score)





