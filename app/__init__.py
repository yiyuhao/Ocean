from flask import Flask
from celery import Celery
from config import config, Config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_moment import Moment
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES


bootstrap = Bootstrap()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)
moment = Moment()
mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
photo_upload = UploadSet('PHOTOS', IMAGES)


def create_app(config_name):
    app = Flask(__name__)

    # 导入配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化插件
    bootstrap.init_app(app)
    celery.conf.update(app.config)
    moment.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    # 将config注册到UploadSet实例photos
    configure_uploads(app, photo_upload)

    # 注册蓝图
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api_develop import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/develop')

    # 将所有请求重定向至安全HTTP
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    return app
