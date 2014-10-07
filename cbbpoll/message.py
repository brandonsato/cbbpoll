from flask import render_template
from flask.ext.mail import Message
from cbbpoll import app, mail, bot
from decorators import async

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

@async
def send_async_pm(recipient, subject, msg):
    with app.app_context():
        bot.send_message(recipient, subject, msg)

def send_email(subject, recipients, template, **kwargs):
    msg = Message(subject, sender = app.config['MAIL_FROM'], recipients = recipients)
    msg.body = render_template(template + '.txt', **kwargs)
    #msg.html = html_body
    send_async_email(app, msg)

def send_reddit_pm(recipient, subject, template, **kwargs):
    msg = render_template(template+'.md', **kwargs)
    send_async_pm(recipient, subject, msg)
