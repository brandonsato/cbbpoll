from flask import render_template
from flask.ext.script import Manager
from cbbpoll import app, message, r
from models import User, Poll, Ballot
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

# These are meant to be run hourly, more frequently than that will result in multiple reminders being sent

ReminderCommand = Manager(usage='Send reminders for pollsters to submit ballots')

def generate_reminders():
    (poll_type, subject, template, users, recipients) = (None, None, None, [], [])
    poll = Poll.query.filter(and_(Poll.openTime < datetime.utcnow(), Poll.openTime > datetime.utcnow() - timedelta(hours=100000))).first()
    if poll:
        poll_type = 0 #new poll
    else:
        poll = Poll.query.filter(and_(Poll.closeTime < datetime.utcnow()+timedelta(hours=12), Poll.closeTime > datetime.utcnow()+timedelta(hours=11))).first()
        if poll:
            poll_type = 1 #closing poll
    if poll:
        email_users = User.query.filter(and_(User.emailReminders == True, User.emailConfirmed == True))
        email_list = email_users.all()
        pollsters = User.query.filter(or_(User.role =='p', User.role == 'a'))
        pm_users = User.query.filter(User.pmReminders == True)
        pm_list = pollsters.union(pm_users).all()

        if poll_type == 0: #new poll
            subject = "[/r/CollegeBasketball] User "+str(poll)+" is Open for Ballot Submission!"
            template = "_remind_open"
        elif poll_type == 1: #closing poll
            subject = "[/r/CollegeBasketball] REMINDER: User "+str(poll)+" is Closing Soon"
            template = "_remind_close"
    return {'poll': poll, 'type':poll_type, 'subject': subject, 'template': template, 'pm_list': pm_list, 'email_list': email_list}

@ReminderCommand.command
def viaEmail():
    reminders = generate_reminders()
    for user in reminders['email_list']:
        message.send_email(reminders['subject'], [user.email], 'email'+reminders['template'], user=user, poll=reminders['poll'])

@ReminderCommand.command
def viaRedditPM():
    reminders= generate_reminders()
    for user in reminders['pm_list']:
        message.send_reddit_pm(user.nickname, reminders['subject'], 'pm'+reminders['template'], user=user, poll=reminders['poll'])
