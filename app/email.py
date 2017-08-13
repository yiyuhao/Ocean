from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import celery, mail


def send_async_email(app, msg):
    # flask-mail的send()使用current_app，所以在不同线程执行mail.send()时，必须人工创建上下文
    # 使用celery可不用创建上下文
    with app.app_context():
        mail.send(msg)


@celery.task
def celery_send_mail(to, subject, template):
    app = current_app._get_current_object()
    msg = Message(subject='{head} - {subject}'.format(head=app.config['MAIL_SUBJECT_PREFIX'], subject=subject),
                  recipients=[to],
                  body=render_template('{}.txt'.format(template), **kwargs),
                  html=render_template('{}.html'.format(template), **kwargs),
                  sender=app.config['MAIL_SENDER'])
    mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject='{head} - {subject}'.format(head=app.config['MAIL_SUBJECT_PREFIX'], subject=subject),
                  recipients=[to],
                  body=render_template('{}.txt'.format(template), **kwargs),
                  html=render_template('{}.html'.format(template), **kwargs),
                  sender=app.config['MAIL_SENDER'])
    # 生产环境使用celery
    if app.config['CELERY_BROKER_URL']:
        celery_send_mail.delay(to, subject, template)
    else:
        th = Thread(target=send_async_email, name='send email', args=[app, msg])
        th.start()
