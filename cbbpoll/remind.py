from flask.ext.script import Manager
from cbbpoll import app, message
from models import User, Poll

# These are meant to be run hourly, more frequently than that will result in multiple reminders being sent

ReminderCommand = Manager(usage='Send reminders for voters to submit ballots')


# Needs a rewrite
def generate_reminders():
    (poll_type, subject, template, email_list, pm_list) = (None, None, None, [], [])
    poll = Poll.query.filter(Poll.recently_opened == True).first()
    if poll:
        poll_type = 0 # new poll
    else:
        poll = Poll.query.filter(Poll.closing_soon == True).first()
        if poll:
            poll_type = 1 # closing poll
    if poll:
        email_list = User.query.filter(User.remind_viaEmail == True).all()
        pm_list = User.query.filter(User.remind_viaRedditPM == True).all()

        if poll_type == 0: # new poll
            subject = "[/r/CollegeBasketball] User "+str(poll)+" is Open for Ballot Submission!"
            template = "_remind_open"
        elif poll_type == 1: # closing poll
            subject = "[/r/CollegeBasketball] REMINDER: User "+str(poll)+" is Closing Soon"
            template = "_remind_close"
    return {'poll': poll, 'type':poll_type, 'subject': subject, 'template': template, 'pm_list': pm_list, 'email_list': email_list}


@ReminderCommand.command
def viaEmail():
    reminders = generate_reminders()
    for user in reminders['email_list']:
        message.send_email(reminders['subject'],
                           [user.email],
                           'email'+reminders['template'],
                           user=user,
                           poll=reminders['poll'])


@ReminderCommand.command
def viaRedditPM():
    reminders= generate_reminders()
    for user in reminders['pm_list']:
        message.send_reddit_pm(user.nickname,
                               reminders['subject'],
                               'pm'+reminders['template'],
                               user=user,
                               poll=reminders['poll'])
