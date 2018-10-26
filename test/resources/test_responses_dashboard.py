import json
from unittest import TestCase, mock

from rm_reporting import app


class TestResponseDashboard(TestCase):

    def setUp(self):
        self.test_client = app.test_client()

    @mock.patch('rm_reporting.app.db.engine')
    def test_dashboard_SEFT_report_success(self, mock_engine):
        mock_engine.execute.return_value.first.return_value = {
            'Sample Size': 100,
            'Total Enrolled': 50,
            'Total Pending': 10,
            'Not Started': 70,
            'In Progress': 20,
            'Complete': 10
        }
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/SEFT/collection-exercise/33db9feb-bed0-46e8-bcb1-3a0373224cd3')
        response_dict = json.loads(response.data)

        self.assertEqual(100, response_dict['report']['sampleSize'])
        self.assertEqual(50, response_dict['report']['accountsEnrolled'])
        self.assertEqual(30, response_dict['report']['downloads'])
        self.assertEqual(10, response_dict['report']['uploads'])

    @mock.patch('rm_reporting.app.db.engine')
    def test_dashboard_SEFT_report_invalid_id(self, mock_engine):
        mock_engine.execute.return_value.first.return_value = {
            'Sample Size': 100,
            'Total Enrolled': 50,
            'Total Pending': 10,
            'Not Started': 100,
            'In Progress': 30,
            'Complete': None
        }
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/SEFT/collection-exercise/00000000-0000-0000-0000-000000000000')
        error_response = json.loads(response.data)['message']

        self.assertEqual(response.status_code, 404)
        self.assertEqual(error_response, 'Invalid collection exercise ID')

    def test_dashboard_SEFT_report_malformed_id(self):
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/SEFT/collection-exercise/not-a-valid-uuid-format')
        error_response = json.loads(response.data)['message']

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, 'Malformed collection exercise ID')

    @mock.patch('rm_reporting.app.db.engine')
    def test_dashboard_EQ_report_success(self, mock_engine):
        mock_engine.execute.return_value.first.return_value = {
            'Sample Size': 100,
            'Total Enrolled': 50,
            'Total Pending': 10,
            'Not Started': 70,
            'In Progress': 20,
            'Complete': 10
        }
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/EQ/collection-exercise/33db9feb-bed0-46e8-bcb1-3a0373224cd3')
        response_dict = json.loads(response.data)

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response_dict['report']['sampleSize'])
        self.assertEqual(50, response_dict['report']['accountsEnrolled'])
        self.assertEqual(10, response_dict['report']['accountsPending'])
        self.assertEqual(10, response_dict['report']['completed'])
        self.assertEqual(20, response_dict['report']['inProgress'])
        self.assertEqual(70, response_dict['report']['notStarted'])

    @mock.patch('rm_reporting.app.db.engine')
    def test_dashboard_EQ_report_invalid_id(self, mock_engine):
        mock_engine.execute.return_value.first.return_value = {
            'Sample Size': 100,
            'Total Enrolled': 50,
            'Total Pending': 10,
            'Not Started': 100,
            'In Progress': 30,
            'Complete': None
        }
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/EQ/collection-exercise/00000000-0000-0000-0000-000000000000')
        error_response = json.loads(response.data)['message']

        self.assertEqual(response.status_code, 404)
        self.assertEqual(error_response, 'Invalid collection exercise ID')

    def test_dashboard_EQ_report_malformed_id(self):
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/EQ/collection-exercise/not-a-valid-uuid-format')
        error_response = json.loads(response.data)['message']

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, 'Malformed collection exercise ID')

    def test_invalid_collection_instrument_type_returns_404(self):
        response = self.test_client.get(
            '/reporting-api/v1/response-dashboard/NOT_VALID/collection-exercise/00000000-0000-0000-0000-000000000000')

        self.assertEqual(404, response.status_code)
        self.assertEqual('Invalid collection instrument type', json.loads(response.data)['message'])
