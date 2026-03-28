import unittest

from auth_utils import AuthPayloadError, normalize_local_storage_payload


class NormalizeLocalStoragePayloadTests(unittest.TestCase):
    def test_accepts_flat_mapping(self):
        payload = {"token": "abc", "uid": 1001}
        normalized = normalize_local_storage_payload(payload)
        self.assertEqual(normalized, {"token": "abc", "uid": "1001"})

    def test_accepts_storage_state_like_payload(self):
        payload = {
            "cookies": [],
            "origins": [
                {
                    "origin": "https://jimeng.jianying.com",
                    "localStorage": [
                        {"name": "token", "value": "abc"},
                        {"name": "refresh", "value": "xyz"},
                    ],
                }
            ],
        }
        normalized = normalize_local_storage_payload(payload)
        self.assertEqual(normalized, {"token": "abc", "refresh": "xyz"})

    def test_rejects_invalid_payload(self):
        with self.assertRaises(AuthPayloadError):
            normalize_local_storage_payload(["invalid"])


if __name__ == "__main__":
    unittest.main()
