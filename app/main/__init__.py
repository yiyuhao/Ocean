from flask import Blueprint, current_app

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_context():
    return dict(Permission=Permission,
                current_app=current_app)
