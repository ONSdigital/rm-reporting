import logging
import os
import unittest

import pytest
from structlog import wrap_logger
from testfixtures import log_capture

from rm_reporting.logger_config import logger_initial_config

# Supresses the warnings that won't be fixed by the project maintainer until Python 2 is deprecated.
# More information about this can be found https://github.com/Simplistix/testfixtures/pull/54
# Remove this and the filterwarnings if this problem ever gets fixed.
testfixtures_warning = "inspect.getargspec()"


class TestLoggerConfig(unittest.TestCase):
    @pytest.mark.filterwarnings(f"ignore:{testfixtures_warning}")
    @log_capture()
    def test_success(self, logs):
        os.environ["JSON_INDENT_LOGGING"] = "1"
        logger_initial_config(service_name="rm-reporting")
        logger = wrap_logger(logging.getLogger())
        logger.error("Test")
        message = logs.records[0].msg

        message_contents = '{\n "event": "Test",\n "severity": "error",\n "level": "error",\n "service": "rm-reporting"'
        self.assertIn(message_contents, message)

    @pytest.mark.filterwarnings(f"ignore:{testfixtures_warning}")
    @log_capture()
    def test_indent_type_error(self, logs):
        os.environ["JSON_INDENT_LOGGING"] = "abc"
        logger_initial_config(service_name="rm-reporting")
        logger = wrap_logger(logging.getLogger())
        logger.error("Test")
        message = logs.records[0].msg
        self.assertIn('{"event": "Test", "severity": "error", "level": "error", "service": "rm-reporting"', message)

    @pytest.mark.filterwarnings(f"ignore:{testfixtures_warning}")
    @log_capture()
    def test_indent_value_error(self, logs):
        logger_initial_config(service_name="rm-reporting")
        logger = wrap_logger(logging.getLogger())
        logger.error("Test")
        message = logs.records[0].msg
        self.assertIn('{"event": "Test", "severity": "error", "level": "error", "service": "rm-reporting"', message)
