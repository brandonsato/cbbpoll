from datetime import datetime, timedelta
from cbbpoll import db, app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    nickname = db.Column(db.String(20), index = True)
    email = db.Column(db.String(120), index = True)
    emailConfirmed = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum('u','p','a'), default = 'u')
    accessToken = db.Column(db.String(30))
    refreshToken = db.Column(db.String(30))
    refreshAfter = db.Column(db.DateTime)
    emailReminders = db.Column(db.Boolean, default=False)
    pmReminders = db.Column(db.Boolean, default=False)
    flair = db.Column(db.Integer, db.ForeignKey('team.id'))
    ballots = db.relationship('Ballot', backref = 'pollster', lazy = 'dynamic', cascade="all, delete-orphan",
                    passive_deletes=True)
    
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

    def is_pollster(self):
        return self.role == 'p' or self.role == 'a'

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

    def __repr__(self):
        return '<User %r>' % (self.nickname)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id', ondelete='CASCADE'))
    votes = db.relationship('Vote', backref = 'fullballot', lazy = 'joined', cascade="all, delete-orphan",
                    passive_deletes=True)
    is_provisional = db.Column(db.Boolean, default = False)

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

