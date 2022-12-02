import json
from unittest import TestCase, mock

from rm_reporting import app


class Row(object):
    """
    This is going represent a row returned from SqlAlchemy.  It's not a true representation, but creating a LegacyRow
    in a matching format is incredibly difficult.  We'll just setattr what we need against it, and then it becomes a
    close enough approximation
    """

    pass


class TestResponseDashboard(TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    @mock.patch("rm_reporting.resources.responses_dashboard.get_report_figures")
    def test_dashboard_report_success(self, mock_reporting_figures):
        mock_reporting_figures.return_value = {
            "sampleSize": 100,
            "accountsEnrolled": 50,
            "accountsPending": 10,
            "notStarted": 70,
            "inProgress": 20,
            "completed": 10,
        }
        response = self.test_client.get(
            "/reporting-api/v1/response-dashboard/survey/57586798-74e3-49fd-93da-a782ec5f5129"
            "/collection-exercise/33db9feb-bed0-46e8-bcb1-3a0373224cd3"
        )
        response_dict = json.loads(response.data)

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response_dict["report"]["sampleSize"])
        self.assertEqual(50, response_dict["report"]["accountsEnrolled"])
        self.assertEqual(10, response_dict["report"]["accountsPending"])
        self.assertEqual(10, response_dict["report"]["completed"])
        self.assertEqual(20, response_dict["report"]["inProgress"])
        self.assertEqual(70, response_dict["report"]["notStarted"])

    @mock.patch("rm_reporting.controllers.case_controller.get_exercise_completion_stats")
    def test_dashboard_report_invalid_id(self, mock_function):

        returned_row = Row()
        setattr(returned_row, "Sample Size", 0)
        setattr(returned_row, "In Progress", 0)
        setattr(returned_row, "Not Started", 0)
        setattr(returned_row, "Complete", 0)

        mock_function.return_value = [returned_row]
        response = self.test_client.get(
            "/reporting-api/v1/response-dashboard/survey/57586798-74e3-49fd-93da-a782ec5f5129"
            "/collection-exercise/00000000-0000-0000-0000-000000000000"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 404)
        self.assertEqual(error_response, "Invalid collection exercise or survey ID")

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
