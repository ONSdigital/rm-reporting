import json
import unittest
from unittest import mock

from rm_reporting import app


class TestResponseDashboard(unittest.TestCase):

    report_details = {
        'Sample Size': 100,
        'Total Enrolled': 50,
        'Total Downloaded': 30,
        'Total Uploaded': 10
    }

    def setUp(self):
        self.test_client = app.test_client()

    @mock.patch('rm_reporting.app.db.engine')
    def test_dashboard_report_success(self, mock_engine):
        mock_engine.execute.return_value.first.return_value = self.report_details
        response = self.test_client.get('/reporting-api/v1/response-dashboard/33db9feb-bed0-46e8-bcb1-3a0373224cd3')
        response_dict = json.loads(response.data)
        self.assertEqual(100, response_dict['report']['sampleSize'])
        self.assertEqual(50, response_dict['report']['accountsEnrolled'])
        self.assertEqual(30, response_dict['report']['downloads'])
        self.assertEqual(10, response_dict['report']['uploads'])

    def test_dashboard_report_invalid_id(self):
        response = self.test_client.get('/reporting-api/v1/response-dashboard/not_a_valid_id')
        self.assertEqual(response.status_code, 400)
