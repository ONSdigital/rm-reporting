import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_restplus import Api

from rm_reporting.logger_config import logger_initial_config

app = Flask(__name__)

app_config = f"config.{os.environ.get('APP_SETTINGS', 'Config')}"
app.config.from_object(app_config)

app.url_map.strict_slashes = False

logger_initial_config(service_name='rm-reporting', log_level=app.config['LOGGING_LEVEL'])
logger = logging.getLogger(__name__)


CORS(app)

api = Api(title='rm-reporting', default='info', default_label="")

from rm_reporting.resources.info import Info  # NOQA # pylint: disable=wrong-import-position

api.init_app(app)
