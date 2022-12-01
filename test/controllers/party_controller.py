from unittest import TestCase

from rm_reporting.controllers import party_controller

survey_id = "0b1e95dd-c84b-4ce3-a6b1-fe6802e4bda0"


class TestPartyController(TestCase):
    def test_get_enrolment_data_empty_string(self):
        test_business_ids = ""
        expected_output = []
        test_output = party_controller.get_enrolment_data(survey_id, test_business_ids)
        self.assertEqual(expected_output, test_output)

    def test_get_respondent_ids_from_enrolment_data_empty_string(self):
        test_input = []
        expected_output = ""
        test_output = party_controller.get_respondent_ids_from_enrolment_data(test_input)
        self.assertEqual(expected_output, test_output)

    def test_get_respondent_data_empty_string(self):
        test_input = ""
        expected_output = {}
        test_output = party_controller.get_respondent_data(test_input)
        self.assertEqual(expected_output, test_output)
