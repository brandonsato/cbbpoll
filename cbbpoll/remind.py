from flask import render_template
from flask.ext.script import Manager
from cbbpoll import app, email
from models import User, Poll

# These are meant to be run hourly, more frequently than that will result in multiple reminders being sent

ReminderCommand = Manager(usage='Send reminders for pollsters to submit ballots')

@ReminderCommand.command
def viaEmail():
    polls = Poll.query.all()
    new_poll, closing_poll = None, None
    for poll in polls:
        if poll.closing_three_days():
            new_poll = poll
        if poll.closing_twelve_hours():
            closing_poll = poll    
    if new_poll or closing_poll:
        users = User.query.all()
        recipients = []
        for user in users:
            if user.is_pollster() and user.email and user.emailConfirmed:
                recipients.append(user)
        if recipients:
            if new_poll:
                for user in recipients:
                    print 'sending open email'
                    email.send_email("[/r/CollegeBasketball] User "+str(new_poll)+" is Open for Ballot Submission!", 
                    [user.email], 'email_remind_open', user=user, poll = new_poll)
            if closing_poll:
                for user in recipients:
                    print 'sending close email'
                    email.send_email("[/r/CollegeBasketball] REMINDER: User "+str(closing_poll)+" is Closing Soon", 
                    [user.email], 'email_remind_close', user=user, poll = closing_poll)

@ReminderCommand.command
def viaRedditPM():
    pass
