from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from ..models import User, Role, Post, Permission
from app import db
from app.decorators import admin_required
from flask import render_template, abort, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if form.validate_on_submit() and current_user.can(Permission.WRITE_ARTICLES):
        post = Post(post_title=form.post_title.data,
                    post_body=form.post_body.data,
                    user=current_user._get_current_object())
        db.session.add(post)
        flash('发表成功')
        return redirect(url_for('main.index'))
    # 获取文章列表
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.post_create_time.desc()).paginate(
        page=page,
        per_page=current_app.config['OCEAN_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)


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
            # 获取文章列表
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(user=user).order_by(Post.post_create_time.desc()).paginate(
        page=page,
        per_page=current_app.config['OCEAN_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('user/profile.html', user=user, posts=posts, pagination=pagination)


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
