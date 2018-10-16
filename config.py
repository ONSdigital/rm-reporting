import os

from rm_reporting.cloud.cloudfoundry import ONSCloudFoundry

cf = ONSCloudFoundry()


class Config(object):
    DEBUG = False
    TESTING = False
    VERSION = '0.4.0'
    PORT = os.getenv('PORT', 8084)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)

    if cf.detected:
        DATABASE_URI = cf.db.credentials['uri']
    else:
        DATABASE_URI = os.getenv('DATABASE_URI',
                                 'postgres://postgres:postgres@localhost:6432/postgres')


class DevelopmentConfig(Config):
    DEBUG = True
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'DEBUG')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)


class TestingConfig(DevelopmentConfig):
    DEBUG = True
    Testing = True
