from flask import render_template
from flask.ext.script import Manager
from cbbpoll import app, email
from models import User, Poll

#These are meant to be run hourly, more frequently than that will result in multiple reminders being sent

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
            if user.is_pollster() and user.email:
                recipients.append(user.email)
        if recipients:
            if new_poll:
                email.send_email("[/r/CollegeBasketball] REMINDER: User "+str(new_poll)+" is Open for Ballot Submission", 
                    'cbbuserpoll@gmail.com', 
                    recipients, 
                    str(new_poll) + " is open for ballot submission! \n\nGo to http://www.cbbpoll.com to submit your ballot", 
                    str(new_poll) + " is open for ballot submission! \n\nGo to http://www.cbbpoll.com to submit your ballot")
            if closing_poll:
                email.send_email("[/r/CollegeBasketball] REMINDER: User "+str(new_poll)+" is Closing Soon", 
                    'cbbuserpoll@gmail.com', 
                    recipients, 
                    str(new_poll) + " is closing for ballot submission! \n\nGo to http://www.cbbpoll.com to submit your ballot", 
                    str(new_poll) + " is closing for ballot submission! \n\nGo to http://www.cbbpoll.com to submit your ballot")

@ReminderCommand.command
def viaRedditPM():
    pass