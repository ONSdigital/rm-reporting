from unittest import TestCase

from rm_reporting.common.validators import is_valid_uuid


class TestValidators(TestCase):

    def test_valid_uuid(self):
        self.assertTrue(is_valid_uuid('00000000-0000-00000000-000000000000'))

    def test_malformed_uuid(self):
        self.assertFalse(is_valid_uuid('00000000-0000-00000000-000000000000-'))
        self.assertFalse(is_valid_uuid('this-is-not-a-valid-uuid'))
