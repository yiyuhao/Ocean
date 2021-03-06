import os


class Config:
    # 私钥
    SECRET_KEY = os.getenv('SECRET_KEY')

    # 邮件配置
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAIL_SERVER = 'smtp.sina.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = 'Ocean'
    MAIL_SENDER = os.getenv('MAIL_SENDER')
    OCEAN_ADMIN = os.getenv('OCEAN_ADMIN')
    OCEAN_LOGGER_MAILBOX = os.getenv('OCEAN_LOGGER_MAILBOX')

    # 头像上传配置
    UPLOADED_PHOTOS_ALLOW = tuple('jpg jpe jpeg png gif svg bmp'.split())
    UPLOADED_PHOTOS_DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'avatar')

    # 相对路径配置
    STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
    USER_AVATAR_PATH = os.path.join(STATIC_PATH, 'avatar')
    USER_AVATAR_SUBPATH = 'avatar'

    # 文章分页
    OCEAN_POSTS_PER_PAGE = 20
    OCEAN_COMMENTS_PER_PAGE = 20

    # 缓慢查询配置
    OCEAN_SLOW_DB_QUERY_TIME = 0.5
    SQLALCHEMY_RECORD_QUERIES = True

    # 是否启用SSL
    SSL_DISABLE = True

    # celery代理
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')

    # server name
    SERVER_NAME = os.getenv('SERVER_NAME')

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # logging error级别错误
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None):
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=cls.OCEAN_LOGGER_MAILBOX,
            subject=cls.MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

        # 处理代理服务器首部以支持proxy
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


class HerokuConfig(ProductionConfig):
    # 是否启用SSL
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # 输出到stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

        # 处理代理服务器首部以支持proxy
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


# 将日志发给daemon:
class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'heroku': HerokuConfig,

    'default': DevelopmentConfig
}
