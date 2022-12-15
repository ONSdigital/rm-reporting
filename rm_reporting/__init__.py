import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Namespace
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from rm_reporting.logger_config import logger_initial_config


def initialise_db(app):
    app.case_db = create_connection(app.config["CASE_DATABASE_URI"])
    app.party_db = create_connection(app.config["PARTY_DATABASE_URI"])


def create_connection(db_connection_uri):
    engine = create_engine(db_connection_uri, echo=True)
    session = scoped_session(sessionmaker())
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session
    return engine


app = Flask(__name__)

app_config = f"config.{os.environ.get('APP_SETTINGS', 'Config')}"
app.config.from_object(app_config)

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
from rm_reporting.resources.responses_dashboard import ResponseDashboard  # NOQA

api.init_app(app)
