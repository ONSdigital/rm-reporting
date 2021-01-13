import json
from unittest import TestCase, mock

from sqlalchemy.dialects.postgresql import UUID

from rm_reporting import app


class TestSppSendReport(TestCase):

    def setUp(self):
        self.test_client = app.test_client()

    @mock.patch('rm_reporting.app.db.engine')
    def test_dashboard_report_success(self, mock_engine):
        mock_engine.execute.return_value.first.return_value = {
            'Sample Size': 100,
            'Total Enrolled': 50,
            'Total Pending': 10,
            'Not Started': 100,
            'In Progress': 30,
            'Complete': None
        }
        response = self.test_client.post(
            '/spp-reporting-api/v1/spp-reporting/send-report')
        response_dict = json.loads(response.data)

