from test.row_helper import Row
from unittest import TestCase
from uuid import UUID

from rm_reporting.controllers import case_controller


class TestCaseController(TestCase):
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
