from unittest import TestCase

from rm_reporting.common.validators import parse_uuid


class TestValidators(TestCase):

    def test_valid_uuid(self):
        collex_id = parse_uuid('00000000-0000-00000000-000000000000')
        self.assertTrue(collex_id)

    def test_malformed_uuid(self):
        collex_id = parse_uuid('this-is-not-a-valid-uuid')
        self.assertFalse(collex_id)
