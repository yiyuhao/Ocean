from . import db
from . import login_manager
from . import photo_upload
from .utils.file_processing import hash_filename, rsize
from app.exceptions import ValidationError
from app.utils.html_to_text import html_to_text
from app.utils.xss_filter import html_clean
from datetime import datetime
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
import os

# 点赞多对多关系
# ORM - User.upvote_posts Post.upvoters
upvotes = db.Table(
    'upvotes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.post_id')))


class Permission:
    FOLLOW = 0b00000001
    COMMENT = 0b00000010
    WRITE_ARTICLES = 0b00000100
    MANAGE_COMMENTS = 0b00001000
    SET_MODERATOR = 0b00010000
    ADMIN = 0b10000000


class Role(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(32), unique=True)
    role_default = db.Column(db.Boolean, default=False, index=True)
    role_permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role {}>'.format(self.role_name)

    @staticmethod
    def insert_roles():
        roles = {
            # role_name : (permission, default)
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MANAGE_COMMENTS, False),
            'Administrator': (0b11111111, False)
        }
        for r in roles:
            if not Role.query.filter_by(role_name=r).first():
                role = Role(role_name=r, role_default=roles[r][1], role_permissions=roles[r][0])
                db.session.add(role)
        db.session.commit()


class Follow(db.Model):
    """

        =====================================字段说明=====================================
        follower_id             主动关注者
        followed_id             被关注者
        timestamp               关注时间
        =====================================字段说明=====================================

    """
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    """

        =====================================字段说明=====================================
        user_name             昵称
        user_email            注册邮箱，用于登录、找回密码
        user_password_hash    密码hash值
        user_confirmed        用户邮箱确认状态，注册邮箱验证后为True，才可具备操作权限
        user_location         所在地
        user_about_me         一句话介绍
        user_member_since     注册时间
        user_last_seen        上次请求时间
        user_avatar_hash      如'33a7db7_____.jpg'，为uuid
        =====================================字段说明=====================================

    """
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64), unique=True, index=True)
    user_email = db.Column(db.String(64), unique=True, index=True)
    user_password_hash = db.Column(db.String(128))
    user_confirmed = db.Column(db.Boolean, default=False)
    user_location = db.Column(db.String(64))
    user_about_me = db.Column(db.String(512))
    user_member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    user_last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    user_avatar_hash = db.Column(db.String(128))

    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))
    posts = db.relationship('Post', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    upvote_posts = db.relationship('Post',
                                   secondary=upvotes,
                                   backref=db.backref('upvoters', lazy='dynamic'),
                                   lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               # 启用所有cascade选项，且delete-orphan
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.user_name)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.user_email == current_app.config['OCEAN_ADMIN']:
                self.role = Role.query.filter_by(role_name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(role_name='User').first()
        self.user_avatar_hash = '{initials}.jpg'.format(initials=self.user_name[0].upper())
        self.followed.append(Follow(followed=self))

    # 重写UserMixin get_id()
    def get_id(self):
        return self.user_id

    # 密码设置
    @property
    def user_password(self):
        raise AttributeError('user_password属性不可被访问')

    @user_password.setter
    def user_password(self, user_password):
        self.user_password_hash = generate_password_hash(user_password)

    def verify_password(self, user_password):
        return check_password_hash(self.user_password_hash, user_password)

    # 头像设置
    @property
    def user_avatar(self):
        raise AttributeError('user_avatar属性不可被访问')

    @user_avatar.setter
    def user_avatar(self, user_avatar):
        # 创建文件uuid
        filename_hash = hash_filename(user_avatar.filename)
        abs_filename_hash = os.path.join(current_app.config['USER_AVATAR_PATH'], filename_hash)
        # 删除旧头像文件(如果是默认头像则不作处理)
        if len(self.user_avatar_hash) > 10:
            os.remove(os.path.join(current_app.config['USER_AVATAR_PATH'],
                                   self.user_avatar_hash))
        # 保存原图
        photo_upload.save(user_avatar, name=filename_hash)
        # 生成缩略图
        avatar_thumbnail = rsize(abs_filename_hash, 300, 300)
        # 删除原图
        os.remove(abs_filename_hash)
        # 保存缩略图
        avatar_thumbnail.save(abs_filename_hash)
        # 保存图片hash
        self.user_avatar_hash = filename_hash
        db.session.add(self)

    # 根据用户名修改默认头像
    @staticmethod
    def on_changed_user_name(target, value, oldvalue, initiator):
        # 初始化User对象时会先触发on_change事件，此时user_avatar_hash还为None
        # 因此判断avatar_hash is None或用户之前是默认头像时，帮助用户更新默认头像
        user_avatar_hash = 'A.jpg' if target.user_avatar_hash is None else target.user_avatar_hash
        if len(user_avatar_hash) < 10:
            target.user_avatar_hash = '{initials}.jpg'.format(initials=value[0].upper())

    # 注册确认token 及重置密码token
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'user_id': self.user_id})

    def check_confirmation_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data['user_id'] != self.user_id:
            return False
        self.user_confirmed = True
        db.session.add(self)
        return True

    # 更改邮箱token
    def generate_email_change_token(self, new_user_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'user_id': self.user_id, 'new_user_email': new_user_email})

    def change_user_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data['user_id'] != self.user_id:
            return False
        self.user_email = data['new_user_email']
        db.session.add(self)
        return True

    # 权限检查
    def can(self, permissions):
        return self.role is not None and (self.role.role_permissions & permissions) == permissions

    @property
    def is_administrator(self):
        return self.can(Permission.ADMIN)

    # 刷新用户访问
    def refresh_last_seen(self):
        self.user_last_seen = datetime.utcnow()
        db.session.add(self)

    # 生成虚拟用户数据
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(user_name=forgery_py.internet.user_name(),
                     user_email=forgery_py.internet.email_address(),
                     user_password=forgery_py.lorem_ipsum.word(),
                     user_confirmed=True,
                     user_location=forgery_py.address.city(),
                     user_about_me=forgery_py.lorem_ipsum.sentences(),
                     user_member_since=forgery_py.date.datetime(past=True),
                     user_last_seen=forgery_py.date.date(past=True))
            db.session.add(u)
            # 生成的user_name有重复风险
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    # 更新所有用户头像为默认头像
    @staticmethod
    def reset_avatar():
        for user in User.query.all():
            user.user_avatar_hash = '{initials}.jpg'.format(initials=user.user_name[0].upper())
            db.session.add(user)
        db.session.commit()

    # 点赞或取消
    def upvote_or_cancel(self, post):
        if self.is_upvote(post):
            self.upvote_posts.remove(post)
        else:
            self.upvote_posts.append(post)
        db.session.add(self)

    # 检查用户是否给某文章点赞
    def is_upvote(self, post):
        return True if self.upvote_posts.filter_by(post_id=post.post_id).first() else False

    # 关注
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.user_id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return True if self.followed.filter_by(followed_id=user.user_id).first() else False

    def is_followed_by(self, user):
        return True if self.followers.filter_by(follower_id=user.user_id).first() else False

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    # 获取所关注用户的文章
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.user_id).filter(Follow.follower_id == self.user_id)

    # 生成登陆令牌
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'user_id': self.user_id}).decode('ascii')

    # 验证登陆令牌
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['user_id'])

    # 转为json资源
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', user_id=self.user_id, _external=True),
            'user_name': self.user_name,
            'user_member_since': self.user_member_since,
            'user_last_seen': self.user_last_seen,
            'posts': url_for('api.get_user_posts', user_id=self.user_id, _external=True),
            'followed_posts': url_for('api.get_user_posts', user_id=self.user_id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user


db.event.listen(User.user_name, 'set', User.on_changed_user_name)


# 游客权限
class AnonymousUser(AnonymousUserMixin):
    @staticmethod
    def can(permissions):
        return False

    @property
    def is_administrator(self):
        return False

    def is_upvote(self, post):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    """

        =====================================字段说明=====================================
        post_title             文章标题
        post_body              非数据库字段，仅用于缓存
        post_body_html         清理后的html格式字符串
        post_body_text         post_body的纯文本，只包含内容，不含html格式
        post_upvote            点赞数
        post_create_time       发表时间
        =====================================字段说明=====================================

    """
    __tablename__ = 'posts'

    post_id = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String(128), nullable=False)
    post_body_html = db.Column(db.Text, nullable=False)
    post_body_text = db.Column(db.Text)
    post_create_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<Post {post_id},{post_title}...>'.format(post_id=self.post_id, post_title=self.post_title[:10])

    # 生成虚拟文章数据
    @staticmethod
    def generate_fake(count=300):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(post_title=forgery_py.lorem_ipsum.title(),
                     post_body=forgery_py.lorem_ipsum.sentences(randint(1, 50)),
                     post_create_time=forgery_py.date.datetime(past=True),
                     user=u)
            db.session.add(p)
            db.session.commit()

    @property
    def post_body(self):
        raise AttributeError('post_body属性不可 被访问')

    # XSS保护 清理传入的原始html字符串
    @post_body.setter
    def post_body(self, post_body):
        self.post_body_html = html_clean(post_body)

    # html文章内容转换为ASCII纯文本，作为首页文章梗概
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        target.post_body_text = html_to_text(markup=value)

    def to_json(self):
        json_post = {
            'url': url_for('api.get_posts', post_id=self.post_id, _external=True),
            'post_body_html': self.post_body_html,
            'post_body_text': self.post_body_text,
            'post_create_time': self.post_create_time,
            'user_id': url_for('api.get_user', user_id=self.user_id, _external=True),
            'comments': url_for('api.get_comments', post_id=self.post_id, _external=True),
            'comments_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        post_title = json_post.get('post_title')
        post_body = json_post.get('post_body')
        if post_title is None or post_title == '':
            raise ValidationError('post does not have a title')
        if post_body is None or post_body == '':
            raise ValidationError('post does not have a body')
        return Post(post_title=post_title,
                    post_body=post_body)


db.event.listen(Post.post_body_html, 'set', Post.on_changed_body)


class Comment(db.Model):
    """

        =====================================字段说明=====================================
        comment_body             评论主题
        comment_timestamp        时间戳
        comment_disabled         遮盖
        =====================================字段说明=====================================

    """
    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, primary_key=True)
    comment_body = db.Column(db.Text, nullable=False)
    comment_create_time = db.Column(db.DateTime, default=datetime.utcnow)
    comment_disabled = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'))

    @staticmethod
    def generate_fake(count=10000):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        post_count = Post.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p = Post.query.offset(randint(0, post_count-1)).first()
            c = Comment(comment_body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                        user=u,
                        post=p)
            db.session.add(c)
            db.session.commit()

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', comment_id=self.comment_id, _external=True),
            'comment_body': self.comment_body,
            'comment_create_time': self.comment_create_time,
            'comment_disabled': self.comment_disabled,
            'post': url_for('api.get_posts', post_id=self.post_id, _external=True),
            'user': url_for('api.get_user', user_id=self.user_id, _external=True)
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        comment_body = json_comment.get('comment_body')
        if comment_body is None or comment_body == '':
            raise ValidationError('comment does not have a body')
        return Comment(comment_body=comment_body)
