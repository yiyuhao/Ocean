from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, EditPostForm, CommentForm
from ..models import User, Role, Post, Permission, Comment
from app import db
from app.decorators import admin_required, permission_required
from flask import render_template, abort, request, redirect, url_for, flash, current_app, jsonify, make_response
from flask_login import current_user, login_required


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/', methods=['GET', 'POST'])
def index():
    post_form = PostForm()
    if post_form.validate_on_submit() and current_user.can(Permission.WRITE_ARTICLES):
        post = Post(post_title=post_form.post_title.data,
                    post_body=post_form.post_body.data,
                    user=current_user._get_current_object())
        db.session.add(post)
        flash('发表成功')
        return redirect(url_for('main.index'))
    # 获取文章列表
    page = request.args.get('page', 1, type=int)
    # cookie中获取show_followed以显示全部文章或关注用户的文章
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    query = current_user.followed_posts if show_followed else Post.query
    pagination = query.order_by(Post.post_create_time.desc()).paginate(
        page=page,
        per_page=current_app.config['OCEAN_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('index.html', post_form=post_form, posts=posts, pagination=pagination,
                           show_followed=show_followed)


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


@main.route('/article/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(comment_body=form.comment_body.data,
                          post=post,
                          user=current_user._get_current_object())
        db.session.add(comment)
        flash('评论已发布')
        return redirect(url_for('main.post', post_id=post_id, page=-1))

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['OCEAN_COMMENTS_PER_PAGE']
    if page == -1:
        page = (post.comments.count() - 1) // per_page + 1
    pagination = post.comments.order_by(Comment.comment_create_time.asc()).paginate(page=page,
                                                                                    per_page=per_page,
                                                                                    error_out=False)
    comments = pagination.items
    return render_template('post/post.html', post=post, form=form, comments=comments, pagination=pagination)


@main.route('/edit-article/<int:post_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user != current_user and not current_user.is_administrator:
        abort(403)
    form = EditPostForm()
    if form.validate_on_submit():
        post.post_title = form.post_title.data
        post.post_body = form.post_body.data
        db.session.add(post)
        flash('修改成功')
        return redirect(url_for('main.post', post_id=post.post_id))
    form.post_title.data = post.post_title
    form.post_body.data = post.post_body_html
    return render_template('post/edit_post.html', form=form)


@main.route('/upvote')
def upvote():
    """
        处理用户点赞某文章，post_id以参数传入request.args
    :return: (json response)
             {'is_current_user_upvoted': true} 返回用户是否点赞了该文章
    """
    post_id = request.args.get('post_id')
    post = Post.query.get_or_404(post_id)
    current_user.upvote_or_cancel(post)
    return jsonify(is_current_user_upvoted=current_user.is_upvote(post))


@main.route('/follow/<user_name>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(user_name):
    user = User.query.filter_by(user_name=user_name).first()
    if user is None:
        flash('不正确的用户')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('你已经关注过了%s' % user.user_name)
        return redirect(url_for('main.profile', user_name=user_name))
    current_user.follow(user)
    flash('已关注%s' % user.user_name)
    return redirect(url_for('main.profile', user_name=user_name))


@main.route('/unfollow/<user_name>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(user_name):
    user = User.query.filter_by(user_name=user_name).first()
    if user is None:
        flash('不正确的用户')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('你没有关注过%s' % user.user_name)
        return redirect(url_for('main.profile', user_name=user_name))
    current_user.unfollow(user)
    flash('已取消关注%s' % user.user_name)
    return redirect(url_for('main.profile', user_name=user_name))