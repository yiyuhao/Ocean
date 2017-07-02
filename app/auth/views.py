from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, login_required
from ..models import User
from .forms import RegistrationForm, LoginForm
from . import auth
from app import db


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(user_name=form.user_name.data,
                    user_email=form.user_email.data,
                    user_password=form.user_password.data)
        db.session.add(user)
        db.session.commit()
        flash('你已注册成功')
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template("auth/register.html", form=form)


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