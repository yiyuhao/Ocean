from unittest import TestCase
from app import create_app, db
from app.models import User, Role, Permission, AnonymousUser, Post, Follow
from datetime import datetime
from time import sleep


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

    # 用户权限
    def test_user_permissions(self):
        Role.insert_roles()
        self.assertNotEqual(len(Role.query.all()), 0)
        u = User(user_email='example@example.com', user_password='password')
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.MANAGE_COMMENTS))
        self.assertFalse(u.can(Permission.SET_MODERATOR))

    def test_moderator_permissions(self):
        Role.insert_roles()
        self.assertNotEqual(len(Role.query.all()), 0)
        u = User(user_email='example@example.com', user_password='password',
                 role=Role.query.filter_by(role_name='Moderator').first())
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.MANAGE_COMMENTS))
        self.assertFalse(u.can(Permission.SET_MODERATOR))

    def test_admin_permissions(self):
        Role.insert_roles()
        self.assertNotEqual(len(Role.query.all()), 0)
        u = User(user_email=self.app.config['OCEAN_ADMIN'], user_password='admin')
        self.assertTrue(u.can(Permission.SET_MODERATOR))
        self.assertTrue(u.can(Permission.ADMIN))

    def test_anonymous_permissions(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.is_administrator)

    # 检查用户登录时间刷新
    def test_refresh_last_seen(self):
        before_register = datetime.utcnow()
        sleep(1)
        u = User(user_email='example@example.com', user_password='password')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.user_last_seen is not None)
        user_register_time = u.user_last_seen
        # 注册时间晚于服务器时间
        self.assertGreater(user_register_time, before_register)
        sleep(1)
        u.refresh_last_seen()
        # 刷新用户最近登陆时间
        self.assertGreater(u.user_last_seen, user_register_time)

    # 检查点赞
    def test_upvote(self):
        u1 = User(user_email='example1@example.com', user_password='password')
        u2 = User(user_email='example2@example.com', user_password='password')
        u3 = User(user_email='example3@example.com', user_password='password')
        p1 = Post(post_title='title', post_body='body')
        p2 = Post(post_title='title', post_body='body')
        p3 = Post(post_title='title', post_body='body')
        db.session.add_all([u1, u2, u3, p1, p2, p3])
        db.session.commit()
        u1.upvote_or_cancel(p1)
        u1.upvote_or_cancel(p2)
        u2.upvote_or_cancel(p2)
        u2.upvote_or_cancel(p3)
        u3.upvote_or_cancel(p3)
        u3.upvote_or_cancel(p1)
        db.session.commit()

        # 检查点赞关系正确
        self.assertIn(p1, u1.upvote_posts.all())
        self.assertIn(p2, u1.upvote_posts.all())
        self.assertNotIn(p3, u1.upvote_posts.all())
        self.assertIn(p2, u2.upvote_posts.all())
        self.assertIn(p3, u2.upvote_posts.all())
        self.assertNotIn(p1, u2.upvote_posts.all())
        self.assertIn(p3, u3.upvote_posts.all())
        self.assertIn(p1, u3.upvote_posts.all())
        self.assertNotIn(p2, u3.upvote_posts.all())

        self.assertIn(u1, p1.upvoters.all())
        self.assertIn(u1, p2.upvoters.all())
        self.assertNotIn(u1, p3.upvoters.all())
        self.assertIn(u2, p2.upvoters.all())
        self.assertIn(u2, p3.upvoters.all())
        self.assertNotIn(u2, p1.upvoters.all())
        self.assertIn(u3, p3.upvoters.all())
        self.assertIn(u3, p1.upvoters.all())
        self.assertNotIn(u3, p2.upvoters.all())

        # 检查取消点赞
        u1.upvote_or_cancel(p1)
        u2.upvote_or_cancel(p2)
        u3.upvote_or_cancel(p3)
        db.session.commit()

        self.assertNotIn(p1, u1.upvote_posts.all())
        self.assertNotIn(p2, u2.upvote_posts.all())
        self.assertNotIn(p3, u3.upvote_posts.all())
        self.assertNotIn(u1, p1.upvoters.all())
        self.assertNotIn(u2, p2.upvoters.all())
        self.assertNotIn(u3, p3.upvoters.all())

    # 检查关注
    def test_follows(self):
        u1 = User(user_email='example1@example.com', user_password='password')
        u2 = User(user_email='example2@example.com', user_password='password')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        timestamp_before = datetime.utcnow()
        sleep(1)
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        sleep(1)
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u2.followers.count() == 2)
        f = u1.followed.order_by(Follow.timestamp.desc()).first()
        self.assertTrue(f.followed == u2)
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.order_by(Follow.timestamp.desc()).first()
        self.assertTrue(f.follower == u1)
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)
