from flask import render_template
from flask_script import Manager
from cbbpoll import app, bot, db
from models import Poll, Team
from views import generate_results

# The postcompleted command should not be timing-dependent
# and can be run as often as necessary.  We will run it every
# 5 minutes, when minute % 5 == 1.

PostCompletedCommand = Manager(usage='Post completed polls to reddit.')

def unposted_polls():
    polls = Poll.query.filter( (Poll.has_completed == True) & (Poll.redditUrl == None) ).all()
    return polls

def announcement_title(poll):
    week = "Week " + str(poll.week) if poll.week > 0 else "Preseason"
    return "User Poll: " + week

def post_poll(poll):
    results = generate_results(poll)[0]
    text = render_template('reddit_results_post.md', results=results, teams=Team.query, poll=poll)

    submission = bot.subreddit(app.config['REDDIT_SUB']).submit(announcement_title(poll), selftext=text)
    submission.save()
    submission.mod.distinguish(as_made_by='mod')
    submission.mod.sticky()
    submission.mod.approve()
    poll.redditUrl = submission.permalink
    db.session.add(poll)
    db.session.commit()

# At some point might want to use this file to send out PMs/emails announcing results
# to interested users.

@PostCompletedCommand.command
def toReddit():
    polls = unposted_polls()
    for poll in polls:
        print(poll)
        post_poll(poll)
