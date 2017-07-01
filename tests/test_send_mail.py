from app import create_app
from unittest import TestCase
from app.email import send_email
from flask import current_app


class MailSenderTestCase(TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_mail_sending(self):
        # todo
        # Q: 邮件发送不成功
        send_email(to='594451138@qq.com',
                   subject='一封测试邮件',
                   template='email/test_email')
        pass
