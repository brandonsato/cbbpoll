from flask import url_for
from datetime import datetime, timedelta
from cbbpoll import db, app
from cbbpoll.message import send_reddit_pm
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.hybrid import hybrid_property
from flask.ext.sqlalchemy import models_committed
from flask.ext.login import AnonymousUserMixin

def on_models_committed(sender, changes):
    for obj, change in changes:
        if change == 'insert' and hasattr(obj, '__commit_insert__'):
            obj.__commit_insert__()
models_committed.connect(on_models_committed, sender=app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    nickname = db.Column(db.String(20), index = True)
    email = db.Column(db.String(120), index = True)
    emailConfirmed = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum('u', 'a'), default = 'u')
    accessToken = db.Column(db.String(30))
    refreshToken = db.Column(db.String(30))
    refreshAfter = db.Column(db.DateTime)
    emailReminders = db.Column(db.Boolean, default=False)
    pmReminders = db.Column(db.Boolean, default=False)
    flair = db.Column(db.Integer, db.ForeignKey('team.id'))
    ballots = db.relationship('Ballot', backref = 'pollster', lazy = 'dynamic', cascade="all, delete-orphan",
                    passive_deletes=True)
    voterEvents = db.relationship('VoterEvent', backref = 'user', lazy = 'dynamic')

    @hybrid_property
    def remind_viaEmail(self):
        return self.emailConfirmed & self.emailReminders

    @hybrid_property
    def remind_viaRedditPM(self):
        return (self.role == 'p') | (self.role =='a')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        return self.role == 'a'

    @property
    def is_pollster(self):
        #latestEvent = VoterEvent.query.filter_by(user=self).order_by(VoterEvent.timestamp.desc()).first()
        #return latestEvent and latestEvent.is_voter
        return self.was_pollster_at(datetime.utcnow())
    @is_pollster.setter
    def is_pollster(self, value):
        event = VoterEvent(timestamp = datetime.utcnow() - timedelta(seconds = 1), user_id = self.id, is_voter = value)
        db.session.add(event)
        db.session.commit()

    def was_pollster_at(self, timestamp):
        mostRecent = VoterEvent.query.filter_by(user=self) \
            .group_by(VoterEvent.timestamp) \
            .having(VoterEvent.timestamp < timestamp) \
            .order_by(VoterEvent.timestamp.desc()) \
            .first()
        return mostRecent and mostRecent.is_voter

    def get_id(self):
        return unicode(self.id)

    def generate_confirmation_token(self, expiration=3600, email=email):
        s = Serializer(app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id, 'email': email})

    def confirm(self, token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        if data.get('email') == self.email and self.emailConfirmed:
            #Avoid a database write, but don't want to give an error to user.
            return True
        self.email = data.get('email')
        self.emailConfirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def name_with_flair(self, size=30):
        if not self.flair:
            return str(self.nickname)
        return "%s%s" % (self.team.logo_html(size), self.nickname)

    def __repr__(self):
        return '<User %r>' % (self.nickname)

    def __str__(self):
        return str(self.nickname)

class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False

class Poll(db.Model):
    __tablename__ = 'poll'
    id = db.Column(db.Integer, primary_key = True)
    season = db.Column(db.Integer)
    week = db.Column(db.Integer)
    openTime = db.Column(db.DateTime)
    closeTime = db.Column(db.DateTime)
    ballots = db.relationship('Ballot', backref = 'fullpoll', lazy = 'joined', cascade="all, delete-orphan",
                    passive_deletes=True)

    @hybrid_property
    def is_open(self):
        return (datetime.utcnow() > self.openTime) & (datetime.utcnow() < self.closeTime)

    @hybrid_property
    def has_completed(self):
        return (datetime.utcnow() > self.closeTime)

    @hybrid_property
    def recently_opened(self):
        return (self.openTime < datetime.utcnow()) & (self.openTime > datetime.utcnow() - timedelta(hours=1))

    @hybrid_property
    def closing_soon(self):
        return (self.closeTime < datetime.utcnow() + timedelta(hours=12)) & (self.closeTime > datetime.utcnow() + timedelta(hours=11))

    def __repr__(self):
        return '<Poll Week %r of %r>' % (self.week, self.season)

    def __str__(self):
        return 'Poll for Week %r of %r-%r' % (int(self.week), int(self.season-1), int(self.season-2000))

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String(75))
    short_name = db.Column(db.String(50))
    flair = db.Column(db.String(50))
    nickname = db.Column(db.String(50))
    png_name = db.Column(db.String(50))
    conference = db.Column(db.String(50))
    fans = db.relationship('User', backref = 'team')

    def png_url(self, size=30):
        return "http://cdn-png.si.com//sites/default/files/teams/basketball/cbk/logos/%s_%s.png" % (self.png_name, size)

    def logo_html(self, size=30):
        if size == 30 or size == 23:
            return "<span class=logo%s><img src='%s' class='logo%s-%s' alt='%s Logo'></span>" % (size, url_for('static', filename='img/logos_%s.png' % size), size, self.png_name, self.full_name)
        else:
            return "<img src='%s' alt='%s Logo'>" % (self.png_url(size), self.full_name) 

    def __repr__(self):
        if self.short_name:
            return '<Team %r>' % (self.short_name)
        else:
            return '<Team %r>' % (self.full_name)

    def __str__(self):
        if self.short_name:
            return'%s (%s)' % (self.full_name, self.short_name)
        else:
            return self.full_name

class Ballot(db.Model):
    __tablename__ = 'ballot'
    id = db.Column(db.Integer, primary_key = True)
    updated = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id', ondelete='CASCADE'))
    votes = db.relationship('Vote', backref = 'fullballot', lazy = 'joined', cascade="all, delete-orphan",
                    passive_deletes=True)

    @property
    def is_provisional(self):
        return not self.pollster.was_pollster_at(self.fullpoll.closeTime)
    @is_provisional.setter
    def is_provisional(self, value):
        raise AttributeError('is_provisional is not a settable field')

    def __repr__(self):
        return '<Ballot %r>' % (self.id)

    def __str__(self):
        return "%s's Ballot for Week %s of %s-%s" % (self.pollster.nickname, int(self.fullpoll.week), int(self.fullpoll.season-1), int(self.fullpoll.season-2000))

class Vote(db.Model):
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key = True)
    ballot_id = db.Column(db.Integer, db.ForeignKey('ballot.id', ondelete='CASCADE'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    rank = db.Column(db.SmallInteger)
    reason = db.Column(db.String(140))

    def __repr__(self):
        return '<Vote %r on Ballot %r>' % (self.rank, self.ballot_id)

class VoterEvent(db.Model):
    __tablename__ = 'voter_event'
    id = db.Column(db.Integer, primary_key = True)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_voter = db.Column(db.Boolean)

    def __repr__(self):
        return '<VoterEvent %r>' % (self.id)

    def __commit_insert__(self):
        if self.is_voter:
            subj = 'You have been approved for voting on the /r/CollegeBasketball Poll'
            template = 'pm_pollster_granted'
        else:
            subj = 'Your voting privilege has been revoked from the /r/CollegeBasketball Poll'
            template = 'pm_pollster_revoked'
        send_reddit_pm(self.user.nickname, subj, template, user=self.user)

