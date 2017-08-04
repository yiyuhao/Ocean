from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden

one_hour = 3600


auth = HTTPBasicAuth()


@api.route('/get-token/')
def get_token():
    # 安全: 避免使用旧令牌申请新令牌
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify(token=g.current_user.generate_auth_token(expiration=one_hour),
                   expiration=one_hour)


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    # token
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return True if g.current_user else False
    # password
    user = User.query.filter_by(user_email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


# 当前blue_print中所有路由都需要登陆保护，对before_request添加login_required装饰
# 应用到整个blue_print
@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.user_confirmed:
        return forbidden('Unconfirmed account')
