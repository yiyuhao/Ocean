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
    USER_DEFAULT_AVATAR = 'user_default_avatar.png'

    # 文章分页
    OCEAN_POSTS_PER_PAGE = 20
    OCEAN_COMMENTS_PER_PAGE = 20

    # 缓慢查询配置
    OCEAN_SLOW_DB_QUERY_TIME = 0.5
    SQLALCHEMY_RECORD_QUERIES = True

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL')


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


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
