import unittest
from proxy import authorization_is_valid


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.token = "a" * 43

    def test_accepts_valid_bearer_token(self):
        self.assertTrue(authorization_is_valid(f"Bearer {self.token}", self.token))

    def test_accepts_case_insensitive_scheme(self):
        self.assertTrue(authorization_is_valid(f"bearer {self.token}", self.token))

    def test_rejects_missing_header(self):
        self.assertFalse(authorization_is_valid(None, self.token))

    def test_rejects_wrong_token(self):
        self.assertFalse(authorization_is_valid("Bearer wrong", self.token))

    def test_rejects_wrong_scheme(self):
        self.assertFalse(authorization_is_valid(f"Basic {self.token}", self.token))

    def test_rejects_empty_expected_token(self):
        self.assertFalse(authorization_is_valid(f"Bearer {self.token}", ""))


if __name__ == "__main__":
    unittest.main()
