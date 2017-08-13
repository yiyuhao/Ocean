from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import celery, mail


# 开发环境使用线程发送邮件
def multi_thread_send_mail(app, msg):
    # flask-mail的send()使用current_app，所以在不同线程执行mail.send()时，必须人工创建上下文
    with app.app_context():
        mail.send(msg)


# 生产环境使用celery
@celery.task
def send_async_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject='{head} - {subject}'.format(head=app.config['MAIL_SUBJECT_PREFIX'], subject=subject),
                  recipients=[to],
                  body=render_template('{}.txt'.format(template), **kwargs),
                  html=render_template('{}.html'.format(template), **kwargs),
                  sender=app.config['MAIL_SENDER'])
    # flask-mail的send()使用current_app，所以在不同线程执行mail.send()时，必须人工创建上下文
    with app.app_context():
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
        send_async_email.delay(to, subject, template, **kwargs)
    else:
        th = Thread(target=multi_thread_send_mail, name='send email', args=[app, msg])
        th.start()
