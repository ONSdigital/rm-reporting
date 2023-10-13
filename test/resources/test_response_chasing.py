import json
from unittest import TestCase, mock

from rm_reporting import app

COLLECTION_EXERCISE_ID = "33db9feb-bed0-46e8-bcb1-3a0373224cd3"
SURVEY_ID = "57586798-74e3-49fd-93da-a782ec5f5129"


class TestResponseChasing(TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    def test_dashboard_report_malformed_collection_exercise_id(self):
        response = self.test_client.get(
            f"/reporting-api/v1/response-chasing/download-report/csv/not-a-valid-uuid/{SURVEY_ID}"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Malformed collection exercise ID")

    def test_dashboard_report_malformed_survey_id(self):
        response = self.test_client.get(
            f"/reporting-api/v1/response-chasing/download-report/xslx/{COLLECTION_EXERCISE_ID}/not-a-valid-uuid"
        )
        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Malformed survey ID")

    @mock.patch("rm_reporting.resources.response_chasing.create_xslx_report")
    def test_response_chasing_xls(self, create_xslx_report):
        create_xslx_report.return_value.getvalue.return_value = "xslx report data"
        response = self.test_client.get(
            f"/reporting-api/v1/response-chasing/download-report/xslx/{COLLECTION_EXERCISE_ID}/{SURVEY_ID}"
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch("rm_reporting.resources.response_chasing.create_csv_report")
    def test_response_chasing_csv(self, create_csv_report):
        create_csv_report.return_value.getvalue.return_value = "csv report data"
        response = self.test_client.get(
            f"/reporting-api/v1/response-chasing/download-report/csv/{COLLECTION_EXERCISE_ID}/{SURVEY_ID}"
        )

        self.assertEqual(response.status_code, 200)

    def test_response_chasing_unsupported_document_type(self):
        response = self.test_client.get(
            f"/reporting-api/v1/response-chasing/download-report/txt/{COLLECTION_EXERCISE_ID}/{SURVEY_ID}"
        )

        error_response = json.loads(response.data)["message"]

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_response, "Document type not supported")
