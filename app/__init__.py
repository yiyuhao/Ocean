from flask import Flask
from config import config
from flask_bootstrap import Bootstrap


bootstrap = Bootstrap()


def create_app(config_name):
    app = Flask(__name__)

    # 导入配置
    app.config.from_object(config[config_name])

    # 初始化插件
    bootstrap.init_app(app)

    # 注册蓝图
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
