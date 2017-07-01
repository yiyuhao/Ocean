from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject='{head} - {subject}'.format(head=app.config['MAIL_SUBJECT_PREFIX'], subject=subject),
                  recipients=[to],
                  body=render_template('{}.txt'.format(template), **kwargs),
                  html=render_template('{}.html'.format(template), **kwargs),
                  sender=app.config['MAIL_SENDER'])
    th = Thread(target=send_async_email, name='send email', args=[app, msg])
    th.start()

    return th
