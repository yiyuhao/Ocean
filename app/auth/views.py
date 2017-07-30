from flask import render_template, url_for, flash, redirect, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from .forms import RegistrationForm, LoginForm, ChangeEmailForm, ChangePasswordForm, GetBackPasswordForm, \
    PasswordResetForm
from . import auth
from app import db
from app.email import send_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


@auth.before_app_request
def filter_unconfirmed_user():
    if current_user.is_authenticated \
            and not current_user.user_confirmed \
            and 'auth.' not in request.endpoint \
            and 'static' != request.endpoint:
        return redirect(url_for('auth.unconfirmed'))


@auth.before_app_request
def refresh_user_last_seen():
    if current_user.is_authenticated:
        current_user.refresh_last_seen()


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
    # 用户重设密码进行登陆后，帮助用户填写email
    user_email = request.args.get('user_email')
    if user_email:
        form.user_email.data = user_email
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


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = GetBackPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.user_email.data).first()
        if user:
            token = user.generate_confirmation_token()
            send_email(to=user.user_email, subject='重置密码', template='auth/email/get_back_password',
                       user=user, token=token)
        flash('一封确认邮件已发往你的账户：{email}。请前往邮箱确认'.format(email=form.user_email.data))
        return redirect(url_for('auth.login'))
    return render_template('auth/get_back_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except:
        flash('链接已过期，请重新填写邮箱进行密码找回')
        return redirect(url_for('auth.password_reset_request'))
    user = User.query.get_or_404(data['user_id'])
    form = PasswordResetForm()
    if form.validate_on_submit():
        new_password = form.new_password.data
        # 若与旧密码相同，将用户踢到登陆页面
        if user.verify_password(new_password):
            flash('你这什么操作...这就是你的旧密码啊，登陆吧...')
            return redirect(url_for('auth.login', user_email=user.user_email))
        user.user_password = form.new_password.data
        db.session.add(user)
        flash('密码已修改成功，请重新登陆')
        return redirect(url_for('auth.login', user_email=user.user_email))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.user_confirmed:
        flash('你已经确认过邮箱了')
    elif current_user.check_confirmation_token(token):
        flash('你已完成邮箱确认，谢谢')
    else:
        flash('该确认邮件的链接无效，或者过期了')
    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.user_confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/resend_confirmation', methods=['GET', 'POST'])
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(to=current_user.user_email, subject='确认你的账号', template='auth/email/confirm', user=current_user,
               token=token)
    flash('新的一封确认邮件已发往<{user_email}>，请前往邮箱确认。'.format(user_email=current_user.user_email))
    return redirect(url_for('main.index'))


@auth.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    email_form = ChangeEmailForm()
    password_form = ChangePasswordForm(current_user)
    # 防止表单未通过验证 刷新了页面 导致遮盖验证错误提示 传入aria_expanded属性
    form_validate_status = {}
    if email_form.submit_email.data and email_form.is_submitted():
        form_validate_status['email_aria_expanded'] = True
        if email_form.validate():
            # 发送确认邮件
            token = current_user.generate_email_change_token(new_user_email=email_form.new_user_email.data)
            send_email(to=current_user.user_email, subject='确认你的账号', template='auth/email/reconfirm',
                       user=current_user, token=token, new_user_email=email_form.new_user_email.data)
            flash('一封确认邮件已发往<{user_email}>，请前往邮箱进行下一步操作。'.format(user_email=current_user.user_email))
    if password_form.submit_password.data and password_form.is_submitted():
        form_validate_status['password_aria_expanded'] = True
        if password_form.validate():
            current_user.user_password = password_form.new_password.data
            db.session.add(current_user)
            flash('密码已更改，请重新登录')
            logout_user()
            return redirect(url_for('main.index'))

    return render_template('user/account.html',
                           user=current_user,
                           email_aria_expanded=form_validate_status.get('email_aria_expanded', False),
                           password_aria_expanded=form_validate_status.get('password_aria_expanded', False),
                           email_form=email_form,
                           password_form=password_form)


# 重置email
@auth.route('/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    if current_user.change_user_email(token):
        flash('你的Ocean登录邮箱已更改')
    else:
        flash('该确认邮件的链接无效，或者过期了')
    return redirect(url_for('main.index'))
