import json
from unittest import TestCase

from rm_reporting import app


class TestResponseChasing(TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    def test_dashboard_report_malformed_collection_exercise_id(self):
        response = self.test_client.get(
            "/reporting-api/v1/response-chasing/download-report/not-a-valid-uuid/57586798-74e3-49fd-93da-a782ec5f5129"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Malformed collection exercise ID")

    def test_dashboard_report_malformed_survey_id(self):
        response = self.test_client.get(
            "/reporting-api/v1/response-chasing/download-report/33db9feb-bed0-46e8-bcb1-3a0373224cd3/not-a-valid-uuid"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Malformed survey ID")
