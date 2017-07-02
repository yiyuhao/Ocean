from . import db
from . import login_manager
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Role(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(32), unique=True)
    role_default = db.Column(db.Boolean, default=False, index=True)
    role_permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role {}>'.format(self.role_name)


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
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))

    def __repr__(self):
        return '<User {}>'.format(self.user_name)

    @property
    def user_password(self):
        raise AttributeError('user_password属性不可被访问')

    @user_password.setter
    def user_password(self, user_password):
        self.user_password_hash = generate_password_hash(user_password)

    def verify_password(self, user_password):
        return check_password_hash(self.user_password_hash, user_password)

    # 重写UserMixin get_id()
    def get_id(self):
        return self.user_id


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
