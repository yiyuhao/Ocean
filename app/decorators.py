from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permissions):
    def wrapper(f):
        @wraps(f)
        def check_permissions(*args, **kwargs):
            if not current_user.can(permissions):
                abort(403)
            return f(*args, **kwargs)
        return check_permissions
    return wrapper


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
