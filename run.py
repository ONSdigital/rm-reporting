import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from rm_reporting.logger_config import logger_initial_config

from structlog import wrap_logger

from flask import _app_ctx_stack


if not os.getenv('APP_SETTINGS'):
    os.environ['APP_SETTINGS'] = 'DevelopmentConfig'

from rm_reporting import app  # NOQA # pylint: disable=wrong-import-position

logger = wrap_logger(logging.getLogger(__name__))


def initialise_db(app):
    app.db = create_database(app.config['DATABASE_URI'])


def create_database(db_connection):

    def current_request():
        return _app_ctx_stack.__ident_func__()

    engine = create_engine(db_connection, convert_unicode=True, echo=True)
    session = scoped_session(sessionmaker(), scopefunc=current_request)
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session
    return engine


if __name__ == '__main__':
    logger_initial_config(service_name='rm_reporting', log_level=app.config['LOGGING_LEVEL'])
    initialise_db(app)

    logger.info(f"Starting listening on port {app.config['PORT']}")
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=int(app.config['PORT']))
