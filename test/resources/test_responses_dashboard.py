import json
from unittest import TestCase

from rm_reporting import app


class TestResponseDashboard(TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    # @mock.patch("rm_reporting.app.db")
    # def test_dashboard_report_success(self, mock_db):
    #     mock_db.engine.execute.return_value.first.return_value = {
    #         "Sample Size": 100,
    #         "Total Enrolled": 50,
    #         "Total Pending": 10,
    #         "Not Started": 70,
    #         "In Progress": 20,
    #         "Complete": 10,
    #     }
    #     response = self.test_client.get(
    #         "/reporting-api/v1/response-dashboard/survey/57586798-74e3-49fd-93da-a782ec5f5129"
    #         "/collection-exercise/33db9feb-bed0-46e8-bcb1-3a0373224cd3"
    #     )
    #     response_dict = json.loads(response.data)
    #
    #     self.assertEqual(200, response.status_code)
    #     self.assertEqual(100, response_dict["report"]["sampleSize"])
    #     self.assertEqual(50, response_dict["report"]["accountsEnrolled"])
    #     self.assertEqual(10, response_dict["report"]["accountsPending"])
    #     self.assertEqual(10, response_dict["report"]["completed"])
    #     self.assertEqual(20, response_dict["report"]["inProgress"])
    #     self.assertEqual(70, response_dict["report"]["notStarted"])

    # @mock.patch("rm_reporting.app.db")
    # def test_dashboard_report_invalid_id(self, mock_db):
    #     mock_db.engine.execute.return_value.first.return_value = {
    #         "Sample Size": 100,
    #         "Total Enrolled": 50,
    #         "Total Pending": 10,
    #         "Not Started": 100,
    #         "In Progress": 30,
    #         "Complete": None,
    #     }
    #     response = self.test_client.get(
    #         "/reporting-api/v1/response-dashboard/survey/57586798-74e3-49fd-93da-a782ec5f5129"
    #         "/collection-exercise/00000000-0000-0000-0000-000000000000"
    #     )
    #     error_response = json.loads(response.data)["message"]
    #
    #     self.assertEqual(response.status_code, 404)
    #     self.assertEqual(error_response, "Invalid collection exercise or survey ID")

    def test_dashboard_report_malformed_collection_exercise_id(self):
        response = self.test_client.get(
            "/reporting-api/v1/response-dashboard/survey/57586798-74e3-49fd-93da-a782ec5f5129"
            "/collection-exercise/not-a-valid-uuid-format"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Malformed collection exercise ID")

    def test_dashboard_report_malformed_survey_id(self):
        response = self.test_client.get(
            "/reporting-api/v1/response-dashboard/survey/not-a-valid-uuid-format"
            "/collection-exercise/33db9feb-bed0-46e8-bcb1-3a0373224cd3"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Malformed survey ID")
