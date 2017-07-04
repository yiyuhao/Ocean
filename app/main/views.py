from . import main
from .. import photo_upload
from flask import render_template, abort, request, redirect, url_for, flash
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
        try:
            filename = photo_upload.save(request.files['photo'])
        except:
            flash('只能上传图片哦')
        else:
            return redirect(url_for('main.show', name=filename))
    return render_template('user/profile.html', user=user)


@main.route('/photo/<name>')
def show(name):
    if name is None:
        abort(404)
    url = photo_upload.url(name)
    return render_template('show.html', url=url, name=name)
