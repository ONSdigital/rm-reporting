import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_restplus import Api, Namespace

from rm_reporting.logger_config import logger_initial_config
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import _app_ctx_stack

def initialise_db(app):
    app.db = create_connection(app.config['DATABASE_URI'])


def create_connection(db_connection_uri):

    def current_request():
        return _app_ctx_stack.__ident_func__()

    engine = create_engine(db_connection_uri, convert_unicode=True, echo=True)
    session = scoped_session(sessionmaker(), scopefunc=current_request)
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session
    return engine


app = Flask(__name__)
logger_initial_config(service_name='rm-reporting', log_level=app.config['LOGGING_LEVEL'])
logger = logging.getLogger(__name__)

app_config = f"config.{os.environ.get('APP_SETTINGS', 'Config')}"
app.config.from_object(app_config)

app.url_map.strict_slashes = False

initialise_db(app)



CORS(app)

api = Api(title='rm-reporting', default='info', default_label="")

response_chasing_api = Namespace('response-chasing', path='/reporting-api/v1/response-chasing')

api.add_namespace(response_chasing_api)

from rm_reporting.resources.info import Info  # NOQA # pylint: disable=wrong-import-position
from rm_reporting.resources.response_chasing import ResponseChasingDownload  # NOQA # pylint: disable=wrong-import-position

api.init_app(app)


