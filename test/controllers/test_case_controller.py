from test.row_helper import Row
from unittest import TestCase, mock
from uuid import UUID

from rm_reporting.controllers import case_controller

exercise_id = "b24a9fd7-0b0d-465f-acf6-cfb8c64e8dfd"

business_1_id = UUID("a9f91050-cd3e-4d29-a14d-67995194fc50")
business_2_id = UUID("71507170-4090-4f73-bd86-224431e11d3e")


class TestCaseController(TestCase):
    @mock.patch("rm_reporting.app.case_db")
    def test_get_all_business_ids_for_collection_exercise(self, mock_engine):
        row_1, row_2 = self._generate_2_case_data_party_id_only_rows()
        mock_engine.engine.execute().all.return_value = [row_1, row_2]
        expected_output = "'a9f91050-cd3e-4d29-a14d-67995194fc50', '71507170-4090-4f73-bd86-224431e11d3e'"
        test_output = case_controller.get_all_business_ids_for_collection_exercise(exercise_id)
        self.assertEqual(expected_output, test_output)

    def test_get_business_ids_from_case_data(self):
        row_1 = Row(party_id=UUID("baefaaef-a2fa-48bc-a2c0-2d58e202253d"))
        row_2 = Row(party_id=UUID("03abc990-4e0f-459e-a3ca-d505fda19299"))
        row_3 = Row(party_id=UUID("e2163f5c-c972-435e-8127-5845a4176358"))
        expected_output = (
            "'baefaaef-a2fa-48bc-a2c0-2d58e202253d', "
            "'03abc990-4e0f-459e-a3ca-d505fda19299', "
            "'e2163f5c-c972-435e-8127-5845a4176358'"
        )
        test_input = [row_1, row_2, row_3]
        test_output = case_controller.get_business_ids_from_case_data(test_input)
        self.assertEqual(expected_output, test_output)

    @mock.patch("rm_reporting.app.case_db")
    def test_get_case_data(self, mock_engine):
        row_1, row_2 = self._generate_2_case_data_rows()
        mock_engine.engine.execute().all.return_value = [row_1, row_2]
        expected_output = [row_1, row_2]
        test_output = case_controller.get_case_data(exercise_id)
        self.assertEqual(expected_output, test_output)

    @mock.patch("rm_reporting.app.case_db")
    def test_get_exercise_completion_stats(self, mock_engine):
        row_1 = Row()
        setattr(row_1, "Sample Size", 100)
        setattr(row_1, "Not Started", 80)
        setattr(row_1, "In Progress", 5)
        setattr(row_1, "Complete", 15)
        mock_engine.engine.execute().all.return_value = [row_1]
        expected_output = [row_1]
        test_output = case_controller.get_exercise_completion_stats(exercise_id)
        self.assertEqual(getattr(expected_output[0], "Sample Size"), getattr(test_output[0], "Sample Size"))
        self.assertEqual(getattr(expected_output[0], "Not Started"), getattr(test_output[0], "Not Started"))
        self.assertEqual(getattr(expected_output[0], "In Progress"), getattr(test_output[0], "In Progress"))
        self.assertEqual(getattr(expected_output[0], "Complete"), getattr(test_output[0], "Complete"))

    @staticmethod
    def _generate_2_case_data_rows() -> tuple[Row, Row]:
        row_1 = Row(party_id=business_1_id, sample_unit_ref="49901111111", status="NOTSTARTED")
        row_2 = Row(party_id=business_2_id, sample_unit_ref="49901111112", status="COMPLETED")
        return row_1, row_2

    @staticmethod
    def _generate_2_case_data_party_id_only_rows() -> tuple[Row, Row]:
        row_1 = Row(party_id=business_1_id)
        row_2 = Row(party_id=business_2_id)
        return row_1, row_2
