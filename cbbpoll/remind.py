from flask import render_template
from flask.ext.script import Manager
from cbbpoll import app, email, r
from models import User, Poll, Ballot
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

# These are meant to be run hourly, more frequently than that will result in multiple reminders being sent

ReminderCommand = Manager(usage='Send reminders for pollsters to submit ballots')

def generate_reminders(self):
    (poll_type, subject, template, users, recipients) = (None, None, None, [], [])
    poll = Poll.query.filter(and_(Poll.openTime < datetime.utcnow(), Poll.openTime > datetime.utcnow() - timedelta(hours=1))).first()
    if poll:
        poll_type = 0 #new poll
    else:
        poll = Poll.query.filter(and_(Poll.closeTime < datetime.utcnow()+timedelta(hours=12), Poll.closeTime > datetime.utcnow()+timedelta(hours=11))).first()
        if poll:
            poll_type = 1 #closing poll
    if poll:
        users = User.query.filter(or_(User.role == 'p',User.role=='a')).all()
        recipients = []
        for user in users:
            if user.email and user.emailConfirmed:
                recipients.append(user)
        if poll_type == 0: #new poll
            subject = "[/r/CollegeBasketball] User "+str(poll)+" is Open for Ballot Submission!"
            template = "_remind_open"
        elif poll_type == 1: #closing poll
            subject = "[/r/CollegeBasketball] REMINDER: User "+str(poll)+" is Closing Soon"
            template = "_remind_close"
    return {'poll': poll, 'type':poll_type, 'subject': subject, 'template': template, 'pollsters': users, 'confirmed_pollsters': recipients}

@ReminderCommand.command
def viaEmail():
    reminders = generate_reminders()
    for user in reminders['recipients']:
        email.send_email(reminders['subject'], [user.email], 'email'+reminders['template'], user=user, poll=reminders['poll'])

@ReminderCommand.command
def viaRedditPM():
    reminders= generate_reminders()
    r.login(app.config['REDDIT_USERNAME'], app.config['REDDIT_PASSWORD'])
    for user in reminders['users']:
        email.send_reddit_pm(user.nickname, reminders['subject'], 'pm'+reminders['template'])
