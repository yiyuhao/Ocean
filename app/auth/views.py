from flask import render_template, url_for, flash, redirect
from ..models import User
from .forms import RegistrationForm
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
        return redirect(url_for('main.index'))
    return render_template("auth/register.html", form=form)
