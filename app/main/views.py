from . import main


@main.route('/')
def index():
    return '<h1>hello!</h1>'