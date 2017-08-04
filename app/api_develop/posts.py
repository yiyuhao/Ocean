from flask import jsonify, request, g, url_for, current_app
from . import api
from .decorators import permission_required
from .errors import forbidden
from .. import db
from ..models import Post, Permission


@api.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page=page,
        per_page=current_app.config['OCEAN_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = url_for('api.get_posts', page=page - 1, _external=True) if pagination.has_prev else None
    next = url_for('api.get_posts', page=page + 1, _external=True) if pagination.has_next else None
    return jsonify(
        posts=[post.to_json() for post in posts],
        prev=prev,
        next=next,
        count=pagination.total)


@api.route('/posts/<int:post_id>')
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_json())


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    post = Post.from_json(request.json)
    post.user = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, {
        'Location': url_for('api.get_post', post_id=post.post_id, _external=True)}


@api.route('/posts/<int:post_id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if g.current_user != post.user and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    post.post_title = request.json.get('post_title', post.post_title)
    post.body = request.json.get('post_body', post.post_body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())
