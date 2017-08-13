from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import celery, mail


# 开发环境使用线程发送邮件
def send_async_email(app, msg):
    # flask-mail的send()使用current_app，所以在不同线程执行mail.send()时，必须人工创建上下文
    with app.app_context():
        mail.send(msg)


# 生产环境使用celery
@celery.task
def multi_thread_send_mail(msg):
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
        multi_thread_send_mail.delay(msg)
    else:
        th = Thread(target=send_async_email, name='send email', args=[app, msg])
        th.start()
