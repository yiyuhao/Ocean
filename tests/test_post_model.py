from unittest import TestCase
from app import create_app, db
from app.models import Post, User


class PostModelTestCase(TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_post_author(self):
        u = User(user_email='example@example.com', user_password='password')
        p = Post(post_title='文章题目', post_body='这是文章的内容.', user=u)
        db.session.add(u)
        db.session.add(p)
        db.session.commit()
        self.assertEqual(p.user_id, u.user_id)
        self.assertTrue(p.user == u)
