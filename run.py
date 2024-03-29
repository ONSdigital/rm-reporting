import logging
import os

from structlog import wrap_logger

from rm_reporting.logger_config import logger_initial_config

if not os.getenv("APP_SETTINGS"):
    os.environ["APP_SETTINGS"] = "DevelopmentConfig"

from rm_reporting import app  # NOQA

logger = wrap_logger(logging.getLogger(__name__))


if __name__ == "__main__":
    logger_initial_config(service_name="rm_reporting", log_level=app.config["LOGGING_LEVEL"])

    logger.info(f"Starting listening on port {app.config['PORT']}")
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=int(app.config["PORT"]))
