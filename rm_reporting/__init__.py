import logging
import os

from flask import Flask, _app_ctx_stack
from flask_cors import CORS
from flask_restx import Api, Namespace
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from rm_reporting.logger_config import logger_initial_config


def initialise_db(app):
    app.db = create_connection(app.config["DATABASE_URI"])
    app.case_db = create_connection(app.config["DATABASE_BINDS"]["case_db"])
    app.party_db = create_connection(app.config["DATABASE_BINDS"]["party_db"])


def create_connection(db_connection_uri):
    def current_request():
        return _app_ctx_stack.__ident_func__()

    engine = create_engine(db_connection_uri, echo=True)
    session = scoped_session(sessionmaker(), scopefunc=current_request)
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session
    return engine


app = Flask(__name__)

app_config = f"config.{os.environ.get('APP_SETTINGS', 'Config')}"
app.config.from_object(app_config)
# supports multiple db connections
app.config["SQLALCHEMY_BINDS"] = app.config["DATABASE_BINDS"]

app.url_map.strict_slashes = False

logger_initial_config(service_name="rm-reporting", log_level=app.config["LOGGING_LEVEL"])
logger = logging.getLogger(__name__)

initialise_db(app)

CORS(app)

api = Api(title="rm-reporting", default="info", default_label="")

response_chasing_api = Namespace("response-chasing", path="/reporting-api/v1/response-chasing")
response_dashboard_api = Namespace("response-dashboard", path="/reporting-api/v1/response-dashboard")

api.add_namespace(response_chasing_api)
api.add_namespace(response_dashboard_api)

from rm_reporting.resources.info import Info  # NOQA
from rm_reporting.resources.response_chasing import ResponseChasingDownload  # NOQA
from rm_reporting.resources.response_chasing import SocialMIDownload  # NOQA
from rm_reporting.resources.responses_dashboard import ResponseDashboard  # NOQA

api.init_app(app)
