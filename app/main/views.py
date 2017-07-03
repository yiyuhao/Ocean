from . import main
from flask import render_template, abort
from datetime import datetime
from ..models import User


@main.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@main.route('/user/<user_name>')
def profile(user_name):
    if not User.query.filter_by(user_name=user_name).first():
        abort(404)
