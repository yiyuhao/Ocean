from . import main
from .. import photo_upload
from app import db
from flask import render_template, abort, request, redirect, url_for, flash, current_app
from datetime import datetime
from ..models import User


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
        user.user_avatar = request.files['photo']
        db.session.add(user)
        db.session.commit()
    user_avatar_uri = url_for('static',
                              filename="{subpath}/{filename}".format(subpath=current_app.config['USER_AVATAR_SUBPATH'],
                                                                     filename=user.user_avatar_hash))
    return render_template('user/profile.html', user=user, user_avatar_url=user_avatar_uri)


@main.route('/photo/<name>')
def show(name):
    if name is None:
        abort(404)
    url = photo_upload.url(name)
    return render_template('show.html', url=url, name=name)
