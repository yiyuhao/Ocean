from . import db
from . import login_manager
from . import photo_upload
from .utils.file_processing import hash_filename, rsize
from datetime import datetime
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
import os


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


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64), unique=True, index=True)
    user_email = db.Column(db.String(64), unique=True, index=True)
    user_password_hash = db.Column(db.String(128))
    user_confirmed = db.Column(db.Boolean, default=False)
    user_location = db.Column(db.String(64))
    user_about_me = db.Column(db.String(64))
    user_member_since = db.Column(db.DateTime(), default=datetime.utcnow())
    user_last_seen = db.Column(db.DateTime(), default=datetime.utcnow())
    user_avatar_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))

    def __repr__(self):
        return '<User {}>'.format(self.user_name)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.user_email == current_app.config['OCEAN_ADMIN']:
                self.role = Role.query.filter_by(role_name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(role_name='User').first()
        self.user_member_since = datetime.utcnow()
        self.user_last_seen = datetime.utcnow()
        self.user_avatar_hash = current_app.config['USER_DEFAULT_AVATAR']

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
        # 删除旧文件
        if current_app.config['USER_DEFAULT_AVATAR'] != self.user_avatar_hash:
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
        # 保存文件
        self.user_avatar_hash = filename_hash

    # 确认token
    def generate_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
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


# 游客权限
class AnonymousUser(AnonymousUserMixin):
    @staticmethod
    def can(permissions):
        return False

    @property
    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
