from . import main
from flask import render_template, abort
from datetime import datetime
from ..models import User


@main.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@main.route('/user/<user_name>')
def profile(user_name):
    user = User.query.filter_by(user_name=user_name).first()
    if user is None:
        abort(404)
    return render_template('user/profile.html', user=user)
