from flask import Flask
from config import config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_moment import Moment
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES


bootstrap = Bootstrap()
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

    # 初始化插件
    bootstrap.init_app(app)
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
    app.register_blueprint(auth_blueprint)

    return app
