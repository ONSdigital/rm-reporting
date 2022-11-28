from unittest import TestCase
from uuid import UUID

from rm_reporting.controllers import case_controller


class Row(object):
    """
    This is going represent a row returned from SqlAlchemy.  It's not a true representation, but creating a LegacyRow
    in a matching format is incredibly difficult.  We'll just setattr what we need against it, and then it becomes a
    close enough approximation
    """

    pass


class TestCaseController(TestCase):
    def test_get_business_ids_from_case_data(self):
        row_1 = Row()
        row_2 = Row()
        row_3 = Row()
        setattr(row_1, "party_id", UUID("baefaaef-a2fa-48bc-a2c0-2d58e202253d"))
        setattr(row_2, "party_id", UUID("03abc990-4e0f-459e-a3ca-d505fda19299"))
        setattr(row_3, "party_id", UUID("e2163f5c-c972-435e-8127-5845a4176358"))
        expected_output = (
            "'baefaaef-a2fa-48bc-a2c0-2d58e202253d', "
            "'03abc990-4e0f-459e-a3ca-d505fda19299', "
            "'e2163f5c-c972-435e-8127-5845a4176358'"
        )
        test_input = [row_1, row_2, row_3]
        test_output = case_controller.get_business_ids_from_case_data(test_input)
        self.assertEqual(expected_output, test_output)
