import uuid
from test.row_helper import Row
from unittest import TestCase, mock

from rm_reporting.controllers import party_controller

survey_id = "0b1e95dd-c84b-4ce3-a6b1-fe6802e4bda0"
exercise_id = "b24a9fd7-0b0d-465f-acf6-cfb8c64e8dfd"

business_1_id = uuid.UUID("a9f91050-cd3e-4d29-a14d-67995194fc50")
business_2_id = uuid.UUID("71507170-4090-4f73-bd86-224431e11d3e")

respondent_1_id = uuid.UUID("98bc4edb-c1ef-4335-8d9e-4ef4a7564f7e")
respondent_2_id = uuid.UUID("877e3b3f-3e5c-4425-b2be-e4cc0b8c2390")
respondent_3_id = uuid.UUID("f4f18cc6-4b1a-4a88-b6c2-ca3cf38f68fe")


class TestPartyController(TestCase):
    def test_format_enrolment_data(self):
        row_1, row_2, row_3 = self._generate_3_enrolment_data_rows()
        test_input = [row_1, row_2, row_3]
        expected_output = {str(business_1_id): [row_1], str(business_2_id): [row_2, row_3]}
        test_output = party_controller.format_enrolment_data(test_input)
        self.assertEqual(expected_output, test_output)

    @mock.patch("rm_reporting.app.party_db")
    def test_get_attribute_data(self, mock_engine):
        row_1 = Row(collection_exercise_uuid=exercise_id, business_party_uuid=business_1_id, business_name="First ltd")
        row_2 = Row(collection_exercise_uuid=exercise_id, business_party_uuid=business_2_id, business_name="2nd ltd")
        mock_engine.engine.execute().all.return_value = [row_1, row_2]
        expected_output = {str(business_1_id): row_1, str(business_2_id): row_2}
        test_output = party_controller.get_attribute_data(exercise_id)
        self.assertEqual(expected_output, test_output)

    @mock.patch("rm_reporting.app.party_db")
    def test_get_enrolment_data(self, mock_engine):
        row_1, row_2, row_3 = self._generate_3_enrolment_data_rows()
        mock_engine.engine.execute().all.return_value = [row_1, row_2, row_3]
        expected_output = [row_1, row_2, row_3]
        business_ids = f"{business_1_id}, {business_2_id}"
        test_output = party_controller.get_enrolment_data(survey_id, business_ids)
        self.assertEqual(expected_output, test_output)

    def test_get_enrolment_data_empty_string(self):
        test_business_ids = ""
        expected_output = []
        test_output = party_controller.get_enrolment_data(survey_id, test_business_ids)
        self.assertEqual(expected_output, test_output)

    def test_get_respondent_ids_from_enrolment_data(self):
        row_1, row_2, row_3 = self._generate_3_enrolment_data_rows()
        test_input = [row_1, row_2, row_3]
        expected_output = f"'{respondent_1_id}', '{respondent_2_id}', '{respondent_3_id}'"
        test_output = party_controller.get_respondent_ids_from_enrolment_data(test_input)
        self.assertEqual(expected_output, test_output)

    def test_get_respondent_ids_from_enrolment_data_empty_string(self):
        test_input = []
        expected_output = ""
        test_output = party_controller.get_respondent_ids_from_enrolment_data(test_input)
        self.assertEqual(expected_output, test_output)

    @mock.patch("rm_reporting.app.party_db")
    def test_get_respondent_data(self, mock_engine):
        row_1, row_2 = self._generate_2_respondent_data_rows()
        mock_engine.engine.execute().all.return_value = [row_1, row_2]
        expected_output = {"1": row_1, "2": row_2}
        respondent_ids = f"{respondent_1_id}, {respondent_2_id}"
        test_output = party_controller.get_respondent_data(respondent_ids)
        self.assertEqual(expected_output, test_output)

    def test_get_respondent_data_empty_string(self):
        test_input = ""
        expected_output = {}
        test_output = party_controller.get_respondent_data(test_input)
        self.assertEqual(expected_output, test_output)

    @staticmethod
    def _generate_2_respondent_data_rows() -> tuple[Row, Row]:
        row_1 = Row(
            id="1",
            party_uuid=respondent_2_id,
            status="ACTIVE",
            email_address="jackjohnson@email.com",
            pending_email_address="",
            first_name="Jack",
            last_name="Johnson",
            telephone="01234123123",
            mark_for_deletion=False,
            created_on="2022-12-04 15:22:20.815615",
            password_verification_token="",
            password_reset_counter=0,
        )
        row_2 = Row(
            id="2",
            party_uuid=respondent_2_id,
            status="ACTIVE",
            email_address="petergriffin@email.com",
            pending_email_address="",
            first_name="Peter",
            last_name="Griffin",
            telephone="01234456456",
            mark_for_deletion=False,
            created_on="2022-12-01 15:22:20.815615",
            password_verification_token="",
            password_reset_counter=0,
        )
        return row_1, row_2

    @staticmethod
    def _generate_3_enrolment_data_rows() -> tuple[Row, Row, Row]:
        row_1 = Row(
            business_id=business_1_id,
            respondent_id=respondent_1_id,
            survey_id=survey_id,
            status="ENABLED",
            created_on="2022-12-05 16:11:20.815615",
        )
        row_2 = Row(
            business_id=business_2_id,
            respondent_id=respondent_2_id,
            survey_id=survey_id,
            status="ENABLED",
            created_on="2022-12-04 15:22:20.815615",
        )
        row_3 = Row(
            business_id=business_2_id,
            respondent_id=respondent_3_id,
            survey_id=survey_id,
            status="PENDING",
            created_on="2022-12-02 13:11:20.815615",
        )
        return row_1, row_2, row_3
