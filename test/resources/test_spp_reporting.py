from unittest import TestCase, mock

from rm_reporting import app


class TestSppSendReport(TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    @mock.patch("rm_reporting.resources.spp_reporting.get_collection_exercise_and_survey")
    @mock.patch("rm_reporting.resources.spp_reporting.get_case_details")
    @mock.patch("rm_reporting.resources.spp_reporting.get_respondent_details")
    @mock.patch("rm_reporting.resources.spp_reporting.GoogleCloudStorageGateway")
    def test_dashboard_report_success(
        self,
        mock_google_cloud_storage_gateway,
        mock_get_respondent_details,
        mock_get_case_details,
        mock_get_collection_exercise_and_survey,
    ):
        mock_get_collection_exercise_and_survey.return_value = [
            "33db9feb-bed0-46e8-bcb1-3a0373224cd3",
            "57586798-74e3-49fd-93da-a782ec5f5129",
        ]
        mock_get_case_details.return_value = [
            "f08998ca-3588-4e41-b9fc-92afe5f97404",
            "49900000001",
            "RUNAME1_COMPANY1 RUNNAME2_COMPANY1",
            "ENABLED",
            "NOTSTARTED",
            "d4ce92a2-6be0-4b65-b9f3-d0a3a94bb5a4",
        ]
        mock_get_respondent_details.return_value = [
            "john doe",
            "07772257772",
            "example@example.com",
            "ACTIVE",
            "ENABLED",
        ]

        response = self.test_client.post("/spp-reporting-api/v1/spp-reporting/send-report")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status, "200 OK")

    @mock.patch("rm_reporting.resources.spp_reporting.get_collection_exercise_and_survey")
    def test_dashboard_report_fail(self, mock_get_collection_exercise_and_survey):
        mock_get_collection_exercise_and_survey.return_value = []

        response = self.test_client.post("/spp-reporting-api/v1/spp-reporting/send-report")
        self.assertEqual(404, response.status_code)
        self.assertEqual("404 NOT FOUND", response.status)
