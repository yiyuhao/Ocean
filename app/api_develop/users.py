from flask import jsonify, request, current_app, url_for
from . import api
from ..models import User, Post


@api.route('/users/<int:user_id>')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_json())


@api.route('/users/<int:user_id>/posts/')
def get_user_posts(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.post_create_time.desc()).paginate(
        page=page,
        # per_page=current_app.config['OCEAN_POSTS_PER_PAGE'],
        per_page=1,
        error_out=False)
    posts = pagination.items
    prev = url_for('api.get_user_posts', user_id=user.user_id, page=page - 1, _external=True) if pagination.has_prev else None
    next = url_for('api.get_user_posts', user_id=user.user_id, page=page + 1, _external=True) if pagination.has_next else None
    return jsonify(
        posts=[post.to_json() for post in posts],
        prev=prev,
        next=next,
        count=pagination.total)


@api.route('/users/<int:user_id>/timeline/')
def get_user_followed_posts(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.post_create_time.desc()).paginate(
        page=page,
        per_page=current_app.config['OCEAN_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = url_for('api.get_user_followed_posts', user_id=user.user_id, page=page - 1, _external=True) if pagination.has_prev else None
    next = url_for('api.get_user_followed_posts', user_id=user.user_id, page=page + 1, _external=True) if pagination.has_prev else None
    return jsonify(
        posts=[post.to_json() for post in posts],
        prev=prev,
        next=next,
        count=pagination.total)
