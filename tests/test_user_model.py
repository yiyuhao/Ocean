from unittest import TestCase
from app import create_app, db
from app.models import User, Role


class UserModelTestCase(TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 密码
    def test_password_setter(self):
        u = User(user_password='password')
        self.assertTrue(u.user_password_hash is not None)

    def test_hash_is_irrelevant_to_password(self):
        u = User(user_password='password')
        self.assertNotIn('password', u.user_password_hash)
        self.assertNotEqual(len('password'), len(u.user_password_hash))

    def test_no_password_getter(self):
        u = User(user_password='password')
        with self.assertRaises(AttributeError):
            print(u.user_password)

    def test_password_verification(self):
        u = User(user_password='password')
        self.assertTrue(u.verify_password('password'))
        self.assertFalse(u.verify_password('pass word'))

    def test_password_salts_are_random(self):
        u1 = User(user_password='password')
        u2 = User(user_password='password')
        self.assertNotEqual(u1.user_password_hash, u2.user_password_hash)

    # 确认token
    def test_generate_confirmation_token(self):
        u = User()
        token = u.generate_confirmation_token()
        self.assertIsNotNone(token)

    def test_confirm_token(self):
        u = User()
        token = u.generate_confirmation_token()
        self.assertTrue(u.check_confirmation_token(token))
        self.assertFalse(u.check_confirmation_token(token={'user_id': 1}))