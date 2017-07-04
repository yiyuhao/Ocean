import os
from flask_uploads import UploadSet, IMAGES, ALL

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

    # 头像上传配置
    UPLOADED_PHOTOS_ALLOW = tuple('jpg jpe jpeg png gif svg bmp'.split())
    UPLOADED_PHOTOS_DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'avatar')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL')


class ProductiongConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductiongConfig,

    'default': DevelopmentConfig
}
