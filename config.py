import os


class Config(object):
    DEBUG = False
    TESTING = False
    VERSION = '1.0.3'
    PORT = os.getenv('PORT', 8084)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)
    DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://postgres:postgres@localhost:5432/ras')
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')


class DevelopmentConfig(Config):
    DEBUG = True
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'DEBUG')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)


class TestingConfig(DevelopmentConfig):
    DEBUG = True
    Testing = True
