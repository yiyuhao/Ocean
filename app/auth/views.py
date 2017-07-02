from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from .forms import RegistrationForm, LoginForm
from . import auth
from app import db
from app.email import send_email


@auth.before_app_request
def filter_unconfirmed_user():
    if current_user.is_authenticated \
            and not current_user.user_confirmed \
            and 'auth.' not in request.endpoint \
            and 'static' != request.endpoint:

        return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.user_email.data).first()
        if user is not None and user.verify_password(form.user_password.data):
            login_user(user, form.remember_me.data)
            # 未登录的用户被login-manager重定向到登陆时，会保存当前地址。用于恢复访问页面
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('邮箱或密码错误')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登陆')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(user_name=form.user_name.data,
                    user_email=form.user_email.data,
                    user_password=form.user_password.data)
        db.session.add(user)
        # 提交注册后才能获得user_id以发送token
        db.session.commit()
        # 发送确认邮件
        token = user.generate_confirmation_token()
        send_email(to=user.user_email, subject='确认你的账号', template='auth/email/confirm', user=user, token=token)
        flash('你已注册成功，一封确认邮件已发往<{user_email}>，请前往邮箱确认。'.format(user_email=user.user_email))
        # 登入用户
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template("auth/register.html", form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.user_confirmed:
        flash('你已经确认过邮箱了')
    elif current_user.check_confirmation_token(token):
        flash('你已完成邮箱确认，谢谢')
    else:
        flash('确认链接无效，或者过期了')
    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.user_confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/resend_confirmation')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(to=current_user.user_email, subject='确认你的账号', template='auth/email/confirm', user=current_user, token=token)
    flash('新的一封确认邮件已发往<{user_email}>，请前往邮箱确认。'.format(user_email=current_user.user_email))
    return redirect(url_for('main.index'))
