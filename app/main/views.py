from . import main
from .forms import EditProfileForm, EditProfileAdminForm
from ..models import User, Role
from app import db
from app.decorators import admin_required
from datetime import datetime
from flask import render_template, abort, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required


@main.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@main.route('/user/<user_name>', methods=['GET', 'POST'])
def profile(user_name):
    user = User.query.filter_by(user_name=user_name).first()
    if user is None:
        abort(404)
    # 头像上传
    if request.method == 'POST' and 'photo' in request.files:
        # 文件类型过滤
        file = request.files['photo']
        suffix = file.filename.split('.')[-1]
        if suffix not in current_app.config['UPLOADED_PHOTOS_ALLOW']:
            flash('你在干什么 只能上传图片啊！')
        else:
            user.user_avatar = file
            db.session.add(user)
            db.session.commit()
    user_avatar_uri = url_for('static',
                              filename="{subpath}/{filename}".format(subpath=current_app.config['USER_AVATAR_SUBPATH'],
                                                                     filename=user.user_avatar_hash))
    return render_template('user/profile.html', user=user, user_avatar_url=user_avatar_uri)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.user_about_me = form.user_about_me.data
        current_user.user_location = form.user_location.data
        db.session.add(current_user)
        return redirect(url_for('main.profile', user_name=current_user.user_name))
    form.user_about_me.data = current_user.user_about_me
    form.user_location.data = current_user.user_location
    return render_template('user/edit_profile.html', form=form)


@main.route('/edit-profile-admin/<int:uid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(uid):
    user = User.query.get_or_404(uid)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.user_name = form.user_name.data
        user.user_email = form.user_email.data
        user.user_confirmed = form.user_confirmed.data
        user.role = Role.query.get(form.role_id.data)
        user.user_about_me = form.user_about_me.data
        user.user_location = form.user_location.data
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.profile', user_name=user.user_name))
    form.user_email.data = user.user_email
    form.user_name.data = user.user_name
    form.user_confirmed.data = user.user_confirmed
    form.role_id.data = user.role_id
    form.user_name.data = user.user_name
    form.user_about_me.data = user.user_about_me
    form.user_location.data = user.user_location
    return render_template('user/edit_profile_admin.html', form=form, user=user)
